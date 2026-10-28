import re
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (QComboBox, QLineEdit, QPushButton, QScrollArea, QSlider, QSpinBox,
                               QVBoxLayout, QWidget)

from ..core import profiles
from ..core.media import ImageOptions, image_info, process_image, target_size
from ..core.platforms import PLATFORMS, PROFILE_PLATFORMS, detect
from ..core.settings import Settings
from ..i18n import t
from . import icons, theme
from .crop_view import CropView
from .jobs import run_async
from .location import SaveLocation
from .login_dialog import sign_in
from .widgets import Card, ProgressLine, Segmented, Toggle, field, hbox, icon_button, label

_FORMATS = [("Orijinal", "original"), ("PNG", "png"), ("JPG", "jpg"), ("WEBP", "webp")]
# crop ratios: (label, width / height or None for free, circle mask)
_RATIOS = [("Serbest", None, False), ("Kare", 1.0, False), ("Daire", 1.0, True), ("16:9", 16 / 9, False),
           ("3:1", 3.0, False), ("4:5", 0.8, False)]
# common target sizes; picking one locks the crop box to that shape and outputs exactly that size
_PRESETS = [
    ("Özel", None),
    ("Profil", (400, 400)),
    ("Profil HD", (1080, 1080)),
    ("YouTube banner", (2560, 1440)),
    ("X kapak", (1500, 500)),
    ("Facebook kapak", (820, 312)),
    ("Instagram gönderi", (1080, 1350)),
    ("Hikâye / Reels", (1080, 1920)),
    ("Video kapağı", (1280, 720)),
]


def _file_name(kind: str) -> str:
    return t("profil") if kind == "avatar" else t("kapak")


class ImagePreview(QWidget):
    def __init__(self, height: int):
        super().__init__()
        self.setFixedHeight(height)
        self.pixmap: QPixmap | None = None
        self.message = ""

    def set_image(self, data: bytes | None, message: str = ""):
        self.pixmap = None
        if data:
            px = QPixmap()
            px.loadFromData(data)
            self.pixmap = px
        self.message = message
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect())
        frame = QPainterPath()
        frame.addRoundedRect(r, 10, 10)
        p.fillPath(frame, QColor(theme.SURFACE_2))
        if not self.pixmap:
            p.setPen(QColor(theme.TEXT_3))
            p.drawText(r.adjusted(16, 0, -16, 0), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                       self.message)
            return
        pw, ph = self.pixmap.width(), self.pixmap.height()
        scale = min((r.width() - 24) / pw, (r.height() - 24) / ph)
        w, h = pw * scale, ph * scale
        target = QRectF(r.center().x() - w / 2, r.center().y() - h / 2, w, h)
        # checkerboard shows transparency (e.g. circle crop)
        p.save()
        p.setClipRect(target)
        cell = 8
        for y in range(int(target.top()), int(target.bottom()) + cell, cell):
            for x in range(int(target.left()), int(target.right()) + cell, cell):
                dark = ((x - int(target.left())) // cell + (y - int(target.top())) // cell) % 2
                p.fillRect(x, y, cell, cell, QColor(255, 255, 255, 10 if dark else 4))
        p.restore()
        p.drawPixmap(target, self.pixmap, QRectF(self.pixmap.rect()))


class AssetCard(Card):
    def __init__(self, title: str, preview_height: int):
        super().__init__(padding=16, radius=12)
        self.include = Toggle(t("Kaydet"), checked=True)
        self.preview = ImagePreview(preview_height)
        self.info = label("", "Caption", wrap=True)
        self.layout().setSpacing(12)
        self.layout().addLayout(hbox(label(title, "H2"), None, self.include))
        self.layout().addWidget(self.preview)
        self.layout().addWidget(self.info)


class ProfilePage(QWidget):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.profile: profiles.Profile | None = None
        self.opts = {"avatar": ImageOptions(), "banner": ImageOptions()}
        self.ratio = {"avatar": 0, "banner": 0}       # index in _RATIOS, -1 when a preset sets the shape
        self.aspect = {"avatar": None, "banner": None}
        self.source: dict[str, QPixmap] = {}
        self.current = "avatar"
        self._syncing = False
        self._generation = {"avatar": 0, "banner": 0}
        self._pending: set[str] = set()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        body = QWidget()
        scroll.setWidget(body)
        root = QVBoxLayout(body)
        root.setContentsMargins(36, 30, 36, 28)
        root.setSpacing(6)
        root.addWidget(label(t("Profil görselleri"), "H1"))
        root.addWidget(label(t("Profil fotoğrafını ve kapak görselini en yüksek çözünürlükte al, "
                               "istersen boyutlandır."), "Sub"))
        root.addSpacing(14)

        # lookup card
        card = Card(padding=18)
        root.addWidget(card)
        c = card.layout()
        c.setSpacing(12)
        self.platform = Segmented([PLATFORMS[k].name for k in PROFILE_PLATFORMS])
        self.platform.changed.connect(self._on_platform)
        self.handle = QLineEdit()
        self.handle.setObjectName("Hero")
        self.handle.setClearButtonEnabled(True)
        self.handle.textChanged.connect(self._on_handle)
        self.handle.returnPressed.connect(self.fetch)
        self.go = QPushButton(t("Getir"))
        self.go.setObjectName("Primary")
        self.go.setIcon(icons.icon("search", "#FFFFFF"))
        self.go.setIconSize(QSize(15, 15))
        self.go.setMinimumHeight(42)
        self.go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.go.clicked.connect(self.fetch)
        self.busy = ProgressLine()
        self.busy.hide()
        self.status = label("", "Caption", wrap=True)
        self.login = QPushButton(" " + t("Giriş yap ve tekrar dene"))
        self.login.setIcon(icons.icon("key", theme.TEXT_2))
        self.login.setIconSize(QSize(15, 15))
        self.login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login.clicked.connect(self._login)
        self.login.hide()
        c.addWidget(self.platform)
        c.addLayout(hbox(self.handle, self.go, stretch=(self.handle,)))
        c.addWidget(self.busy)
        c.addWidget(self.status)
        c.addLayout(hbox(self.login, None))
        c.addWidget(SaveLocation(settings))

        # results
        self.results = QWidget()
        self.results.hide()
        res = QVBoxLayout(self.results)
        res.setContentsMargins(0, 12, 0, 0)
        res.setSpacing(12)
        self.avatar_card = AssetCard(t("Profil fotoğrafı"), 200)
        self.avatar_card.setFixedWidth(300)
        self.banner_card = AssetCard(t("Kapak"), 200)
        res.addLayout(hbox(self.avatar_card, self.banner_card, spacing=12, stretch=(self.banner_card,)))

        edit = Card(padding=18)
        e = edit.layout()
        self.target = Segmented([t("Profil fotoğrafı"), t("Kapak")], height=32)
        self.target.changed.connect(lambda i: self._select("avatar" if i == 0 else "banner"))
        self.crop_view = CropView(340)
        self.crop_view.changed.connect(self._on_box_moving)
        self.crop_view.released.connect(self._on_box_done)

        self.ratio_seg = Segmented([t(name) for name, _, _ in _RATIOS], height=34)
        self.ratio_seg.changed.connect(self._on_ratio)
        self.preset = QComboBox()
        for name, size in _PRESETS:
            self.preset.addItem(t(name) + (f"  ·  {size[0]} × {size[1]}" if size else ""), size)
        self.preset.setMinimumWidth(230)
        self.preset.currentIndexChanged.connect(self._on_preset)

        self.w = QSpinBox()
        self.h = QSpinBox()
        for s in (self.w, self.h):
            s.setRange(1, 10000)
            s.setFixedWidth(92)
            s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s.setSuffix(" px")
            s.setKeyboardTracking(False)  # apply when typing is done, not on every key
        self.w.valueChanged.connect(lambda v: self._on_size("w", v))
        self.h.valueChanged.connect(lambda v: self._on_size("h", v))
        self.lock = icon_button("lock", t("Oranı koru (kapalıyken tam bu boyuta kırpılır)"))
        self.lock.setCheckable(True)
        self.lock.setChecked(True)
        self.lock.toggled.connect(self._on_lock)
        reset = icon_button("retry", t("Kırpmayı ve boyutu sıfırla"))
        reset.clicked.connect(self._reset)
        size_row = QWidget()
        size_row.setLayout(hbox(self.w, label("×", "Caption"), self.h, 2, self.lock, reset, spacing=6))

        self.fmt = QComboBox()
        for text, key in _FORMATS:
            self.fmt.addItem(t(text), key)
        self.fmt.currentIndexChanged.connect(self._on_fmt)
        self.quality = QSlider(Qt.Orientation.Horizontal)
        self.quality.setRange(40, 100)
        self.quality.setFixedWidth(130)
        self.quality.valueChanged.connect(self._on_quality)
        self.quality_value = label("92", "Muted")
        self.quality_value.setFixedWidth(26)
        q_row = QWidget()
        q_row.setLayout(hbox(self.quality, self.quality_value, spacing=10))
        self.quality_field = field(t("Kalite"), q_row)

        e.addLayout(hbox(label(t("Düzenle"), "H2"),
                         label(t("Çerçeveyi sürükle, köşelerinden boyutlandır ya da resmin üstünde yeni bir alan çiz."),
                               "Caption"), None, self.target, spacing=12))
        e.addWidget(self.crop_view)
        e.addLayout(hbox(field(t("Kırpma oranı"), self.ratio_seg), field(t("Hazır boyut"), self.preset), None,
                         spacing=18))
        e.addLayout(hbox(field(t("Çıktı boyutu"), size_row), field(t("Biçim"), self.fmt), self.quality_field,
                         None, spacing=18))
        res.addWidget(edit)

        self.save_btn = QPushButton(t("Kaydet"))
        self.save_btn.setObjectName("Primary")
        self.save_btn.setIcon(icons.icon("download", "#FFFFFF"))
        self.save_btn.setIconSize(QSize(16, 16))
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.save)
        self.saved = label("", "Caption", wrap=True)
        res.addLayout(hbox(self.saved, None, self.save_btn, stretch=(self.saved,)))
        root.addWidget(self.results)
        root.addStretch(1)

        self._debounce = QTimer(self, singleShot=True, interval=140)
        self._debounce.timeout.connect(self._render_pending)
        self._on_platform(0)

    # ------------------------------------------------------------ lookup

    @property
    def platform_key(self) -> str:
        return PROFILE_PLATFORMS[self.platform.index()]

    def _on_platform(self, _):
        hints = {"youtube": t("@kanal ya da kanal bağlantısı"), "reddit": t("u/kullanıcı ya da r/topluluk")}
        self.handle.setPlaceholderText(hints.get(self.platform_key, t("@kullanıcıadı ya da profil bağlantısı")))

    def _on_handle(self, text):
        p = detect(text) if "/" in text or "." in text else None
        if p and p.key in PROFILE_PLATFORMS:
            self.platform.set_index(PROFILE_PLATFORMS.index(p.key))

    def fetch(self):
        text = self.handle.text()
        self.go.setEnabled(False)
        self.busy.show()
        self.busy.set_value(None)
        self._set_status(t("Aranıyor"))
        key, cookies = self.platform_key, self.settings.cookies_browser
        run_async(lambda: profiles.fetch(text, key, cookies), self._fetched, self._fetch_failed, self)

    def _set_status(self, text: str, error: bool = False):
        self.status.setObjectName("Error" if error else "Caption")
        self.status.setText(text)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def _fetch_done(self):
        self.go.setEnabled(True)
        self.busy.hide()
        self.login.hide()

    def _login(self):
        if sign_in(self, self.platform_key, self.settings):
            self.fetch()

    def _fetch_failed(self, msg):
        self._fetch_done()
        self._set_status(msg, error=True)
        self.login.setVisible(profiles.LOGIN_HINT in msg)

    def _fetched(self, prof: profiles.Profile):
        self._fetch_done()
        self.profile = prof
        title = PLATFORMS[prof.platform].name + " · " + (prof.name or prof.handle)
        if prof.name and prof.handle and prof.handle.lower() not in prof.name.lower():
            title += f"  ({prof.handle})"
        self._set_status("\n".join([title, *prof.notes]))
        self.login.setVisible(any(profiles.LOGIN_HINT in n for n in prof.notes))
        self.source.clear()
        for kind, card in (("avatar", self.avatar_card), ("banner", self.banner_card)):
            asset = getattr(prof, kind)
            card.include.setChecked(bool(asset))
            card.include.setEnabled(bool(asset))
            self.ratio[kind], self.aspect[kind] = 0, None
            self.opts[kind] = ImageOptions()
            if asset:
                px = QPixmap()
                px.loadFromData(asset.data)
                self.source[kind] = px
                self.opts[kind].box = (0, 0, px.width(), px.height())
            else:
                card.preview.set_image(None, t("Bu hesapta kapak görseli yok.") if kind == "banner"
                                       else t("Profil fotoğrafı bulunamadı."))
                card.info.setText("")
            self.target.set_disabled(0 if kind == "avatar" else 1, not asset)
        self.results.show()
        self.saved.setText("")
        first = "avatar" if prof.avatar else "banner"
        self.target.set_index(0 if first == "avatar" else 1, animate=False, emit=False)
        self._select(first)
        for kind in ("avatar", "banner"):
            if getattr(prof, kind):
                self._render(kind)

    # ------------------------------------------------------------ editing

    def _asset(self, kind: str):
        return getattr(self.profile, kind) if self.profile else None

    def _src_size(self, kind: str) -> tuple[int, int]:
        px = self.source[kind]
        return px.width(), px.height()

    def _select(self, kind: str):
        if not self._asset(kind):
            return
        self.current = kind
        self.avatar_card.set_highlight(kind == "avatar")
        self.banner_card.set_highlight(kind == "banner")
        o = self.opts[kind]
        self._syncing = True
        self.crop_view.set_image(self.source[kind])
        self.crop_view.aspect = self.aspect[kind]
        self.crop_view.circle = o.crop == "circle"
        self.crop_view.set_box(o.box)
        if self.ratio[kind] >= 0:
            self.ratio_seg.set_index(self.ratio[kind], animate=False, emit=False)
        else:
            self.ratio_seg.clear_selection()
        self.fmt.setCurrentIndex([k for _, k in _FORMATS].index(o.fmt))
        self.quality.setValue(o.quality)
        self.quality_value.setText(str(o.quality))
        self.lock.setChecked(o.keep_ratio)
        self._sync_preset()
        self._syncing = False
        self._sync_size()
        self._sync_quality()

    def _sync_size(self):
        tw, th = target_size(self._src_size(self.current), self.opts[self.current])
        self._syncing = True
        self.w.setValue(tw)
        self.h.setValue(th)
        self._syncing = False

    def _sync_preset(self):
        o = self.opts[self.current]
        size = (o.width, o.height) if not o.keep_ratio else None
        index = next((i for i, (_, s) in enumerate(_PRESETS) if s and s == size), 0)
        was = self._syncing
        self._syncing = True
        self.preset.setCurrentIndex(index)
        self._syncing = was

    def _sync_quality(self):
        o = self.opts[self.current]
        src_ext = image_info(self._asset(self.current).data)[2]
        fmt = src_ext if o.fmt == "original" else o.fmt
        self.quality_field.setVisible(fmt in ("jpg", "webp") and o.crop != "circle")

    def _changed(self):
        self._generation[self.current] += 1
        self._pending.add(self.current)  # switching tabs before the timer fires must not drop it
        self._debounce.start()

    def _render_pending(self):
        for kind in self._pending:
            self._render(kind)
        self._pending.clear()

    def _on_box_moving(self):
        self.opts[self.current].box = self.crop_view.crop_box()
        self._sync_size()

    def _on_box_done(self):
        self._on_box_moving()
        self._changed()

    def _on_ratio(self, index: int):
        if self._syncing or not self.profile:
            return
        _, aspect, circle = _RATIOS[index]
        kind = self.current
        o = self.opts[kind]
        self.ratio[kind], self.aspect[kind] = index, aspect
        self.crop_view.set_aspect(aspect, circle)
        o.box = self.crop_view.crop_box()
        o.crop = "circle" if circle else "none"
        if not o.keep_ratio:  # a preset's exact size no longer fits a new shape
            o.width = o.height = 0
            o.keep_ratio = True
            self.lock.setChecked(True)
        self._sync_preset()
        self._sync_size()
        self._sync_quality()
        self._changed()

    def _on_preset(self, index: int):
        size = _PRESETS[index][1]
        if self._syncing or not self.profile or not size:
            return
        kind = self.current
        o = self.opts[kind]
        aspect = size[0] / size[1]
        self.ratio[kind], self.aspect[kind] = -1, aspect
        self.crop_view.set_aspect(aspect)
        o.box = self.crop_view.crop_box()
        o.width, o.height = size
        o.keep_ratio = False  # exact output size
        o.crop = "none"
        self._select(kind)
        self._changed()

    def _on_size(self, axis: str, value: int):
        if self._syncing or not self.profile:
            return
        o = self.opts[self.current]
        if o.keep_ratio:
            o.width, o.height = (value, 0) if axis == "w" else (0, value)
        elif axis == "w":
            o.width, o.height = value, o.height or self.h.value()
        else:
            o.width, o.height = o.width or self.w.value(), value
        self._sync_size()
        self._sync_preset()
        self._changed()

    def _on_lock(self, on: bool):
        self.lock.setIcon(icons.icon("lock" if on else "unlock", theme.TEXT if on else theme.TEXT_3))
        if self._syncing or not self.profile:
            return
        o = self.opts[self.current]
        o.keep_ratio = on
        if on:
            o.height = 0 if o.width else o.height
        else:
            o.width, o.height = self.w.value(), self.h.value()
        self._sync_size()
        self._sync_preset()
        self._changed()

    def _reset(self):
        if not self.profile:
            return
        kind = self.current
        w, h = self._src_size(kind)
        o = self.opts[kind]
        o.width = o.height = 0
        o.keep_ratio = True
        o.crop = "none"
        o.box = (0, 0, w, h)
        self.ratio[kind], self.aspect[kind] = 0, None
        self._select(kind)
        self._changed()

    def _on_fmt(self, index: int):
        if self._syncing or not self.profile:
            return
        self.opts[self.current].fmt = _FORMATS[index][1]
        self._sync_quality()
        self._changed()

    def _on_quality(self, value: int):
        self.quality_value.setText(str(value))
        if self._syncing or not self.profile:
            return
        self.opts[self.current].quality = value
        self._changed()

    def _render(self, kind: str):
        asset = self._asset(kind)
        if not asset:
            return
        gen = self._generation[kind]
        opts = replace(self.opts[kind])
        data = asset.data
        card = self.avatar_card if kind == "avatar" else self.banner_card
        src_w, src_h, src_ext = image_info(data)

        def done(result):
            if gen != self._generation[kind]:
                return  # a newer edit is on its way
            out, ext = result
            w, h, _ = image_info(out)
            card.preview.set_image(out)
            same = (w, h) == (src_w, src_h) and ext == src_ext
            src = f"{src_w} × {src_h} {src_ext.upper()}"
            dst = f"{w} × {h} {ext.upper()} · {len(out) / 1024:.0f} KB"
            text = dst if same else f"{src}  →  {dst}"
            box = opts.box or (0, 0, src_w, src_h)
            if w > (box[2] - box[0]) * 1.05 or h > (box[3] - box[1]) * 1.05:
                text += "\n" + t("Kaynak bundan küçük; büyütülen görsel bulanık olabilir.")
            card.info.setText(text)

        run_async(lambda: process_image(data, opts), done, lambda m: card.info.setText(m), self)

    # ------------------------------------------------------------ save

    def save(self):
        if not self.profile:
            return
        prof = self.profile
        jobs = [(kind, self._asset(kind).data, replace(self.opts[kind]))
                for kind, card in (("avatar", self.avatar_card), ("banner", self.banner_card))
                if self._asset(kind) and card.include.isChecked()]
        if not jobs:
            self.saved.setText(t("Kaydedilecek görsel seçilmedi."))
            return
        folder = Path(self.settings.output_dir)
        base = re.sub(r'[\\/:*?"<>|\s]+', "_", f"{prof.platform}_{prof.handle}").strip("_")

        def work():
            folder.mkdir(parents=True, exist_ok=True)
            written = []
            for kind, data, opts in jobs:
                out, ext = process_image(data, opts)
                stem = f"{base}_{_file_name(kind)}"
                path = folder / f"{stem}.{ext}"
                n = 2
                while path.exists():
                    path = folder / f"{stem} ({n}).{ext}"
                    n += 1
                path.write_bytes(out)
                written.append(path.name)
            return written

        self.save_btn.setEnabled(False)
        run_async(work, self._saved_ok, self._saved_err, self)

    def _saved_ok(self, names):
        self.save_btn.setEnabled(True)
        self.saved.setText(t("Kaydedildi: {names}", names=", ".join(names)) + "\n" + self.settings.output_dir)

    def _saved_err(self, msg):
        self.save_btn.setEnabled(True)
        self.saved.setText(t("Kaydedilemedi: {error}", error=msg))
