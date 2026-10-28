import re
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (QComboBox, QLineEdit, QPushButton, QScrollArea, QSlider, QSpinBox,
                               QVBoxLayout, QWidget)

from ..core import profiles
from ..core.media import ImageOptions, image_info, process_image, target_size
from ..core.platforms import PLATFORMS, PROFILE_PLATFORMS, detect
from ..core.settings import Settings
from . import icons, theme
from .jobs import run_async
from .login_dialog import sign_in
from .widgets import Card, ProgressLine, Segmented, Toggle, field, hbox, icon_button, label

_PLACEHOLDER = {
    "youtube": "@kanal ya da kanal bağlantısı",
    "reddit": "u/kullanıcı ya da r/topluluk",
}
_CROPS = {
    "avatar": [("Yok", "none"), ("Kare", "square"), ("Daire", "circle")],
    "banner": [("Yok", "none"), ("16:9", "wide"), ("Kare", "square")],
}
_FORMATS = [("Orijinal", "original"), ("PNG", "png"), ("JPG", "jpg"), ("WEBP", "webp")]
_NAMES = {"avatar": "profil", "banner": "kapak"}


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
        frame.addRoundedRect(r, 12, 12)
        p.fillPath(frame, QColor(0, 0, 0, 70))
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
        super().__init__(padding=16, radius=16)
        self.include = Toggle("Kaydet", checked=True)
        self.preview = ImagePreview(preview_height)
        self.info = label("", "Caption")
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
        self.current = "avatar"
        self._syncing = False
        self._generation = {"avatar": 0, "banner": 0}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        body = QWidget()
        scroll.setWidget(body)
        root = QVBoxLayout(body)
        root.setContentsMargins(40, 36, 40, 28)
        root.setSpacing(6)
        root.addWidget(label("Profil görselleri", "H1"))
        root.addWidget(label("Profil fotoğrafını ve kapak görselini en yüksek çözünürlükte al, "
                             "istersen boyutlandır.", "Sub"))
        root.addSpacing(18)

        # lookup card
        card = Card(padding=22)
        root.addWidget(card)
        c = card.layout()
        c.setSpacing(16)
        self.platform = Segmented([PLATFORMS[k].name for k in PROFILE_PLATFORMS])
        self.platform.changed.connect(self._on_platform)
        self.handle = QLineEdit()
        self.handle.setObjectName("Hero")
        self.handle.setClearButtonEnabled(True)
        self.handle.textChanged.connect(self._on_handle)
        self.handle.returnPressed.connect(self.fetch)
        self.go = QPushButton("Getir")
        self.go.setObjectName("Primary")
        self.go.setIcon(icons.icon("search", "#FFFFFF"))
        self.go.setIconSize(QSize(16, 16))
        self.go.setMinimumHeight(46)
        self.go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.go.clicked.connect(self.fetch)
        self.busy = ProgressLine()
        self.busy.hide()
        self.status = label("", "Caption", wrap=True)
        c.addWidget(self.platform)
        c.addLayout(hbox(self.handle, self.go, stretch=(self.handle,)))
        c.addWidget(self.busy)
        self.login = QPushButton(" Giriş yap ve tekrar dene")
        self.login.setIcon(icons.icon("key", theme.TEXT_2))
        self.login.setIconSize(QSize(15, 15))
        self.login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login.clicked.connect(self._login)
        self.login.hide()
        c.addWidget(self.status)
        c.addLayout(hbox(self.login, None))

        # results
        self.results = QWidget()
        self.results.hide()
        res = QVBoxLayout(self.results)
        res.setContentsMargins(0, 18, 0, 0)
        res.setSpacing(14)
        self.avatar_card = AssetCard("Profil fotoğrafı", 220)
        self.avatar_card.setFixedWidth(300)
        self.banner_card = AssetCard("Kapak", 220)
        res.addLayout(hbox(self.avatar_card, self.banner_card, spacing=14, stretch=(self.banner_card,)))

        edit = Card(padding=20)
        e = edit.layout()
        self.target = Segmented(["Profil fotoğrafı", "Kapak"], height=32)
        self.target.changed.connect(lambda i: self._select("avatar" if i == 0 else "banner"))
        self.w = QSpinBox()
        self.h = QSpinBox()
        for s in (self.w, self.h):
            s.setRange(1, 10000)
            s.setFixedWidth(96)
            s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s.setSuffix(" px")
        self.w.valueChanged.connect(lambda v: self._on_size("w", v))
        self.h.valueChanged.connect(lambda v: self._on_size("h", v))
        self.lock = icon_button("lock", "En-boy oranını koru")
        self.lock.setCheckable(True)
        self.lock.setChecked(True)
        self.lock.toggled.connect(self._on_lock)
        reset = icon_button("retry", "Orijinal boyuta dön")
        reset.clicked.connect(self._reset_size)
        size_row = QWidget()
        size_row.setLayout(hbox(self.w, label("×", "Caption"), self.h, 2, self.lock, reset, spacing=6))

        self.fmt = QComboBox()
        for text, key in _FORMATS:
            self.fmt.addItem(text, key)
        self.fmt.currentIndexChanged.connect(self._on_fmt)
        self.quality = QSlider(Qt.Orientation.Horizontal)
        self.quality.setRange(40, 100)
        self.quality.setFixedWidth(150)
        self.quality.valueChanged.connect(self._on_quality)
        self.quality_value = label("92", "Muted")
        self.quality_value.setFixedWidth(26)
        q_row = QWidget()
        q_row.setLayout(hbox(self.quality, self.quality_value, spacing=10))
        self.quality_field = field("Kalite", q_row)
        self.crop = Segmented([t for t, _ in _CROPS["avatar"]], height=36)
        self.crop.changed.connect(self._on_crop)

        e.addLayout(hbox(label("Düzenle", "H2"), None, self.target))
        e.addLayout(hbox(field("Boyut", size_row), field("Kırpma", self.crop), field("Biçim", self.fmt),
                         self.quality_field, None, spacing=22))
        res.addWidget(edit)

        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setObjectName("Primary")
        self.save_btn.setIcon(icons.icon("download", "#FFFFFF"))
        self.save_btn.setIconSize(QSize(17, 17))
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.save)
        self.saved = label("", "Caption")
        open_dir = QPushButton("Klasörü aç")
        open_dir.setObjectName("Link")
        open_dir.setCursor(Qt.CursorShape.PointingHandCursor)
        open_dir.clicked.connect(self._open_dir)
        res.addLayout(hbox(self.saved, None, open_dir, 16, self.save_btn))
        root.addWidget(self.results)
        root.addStretch(1)

        self._debounce = QTimer(self, singleShot=True, interval=140)
        self._debounce.timeout.connect(lambda: self._render(self.current))
        self._on_platform(0)

    # ------------------------------------------------------------ lookup

    @property
    def platform_key(self) -> str:
        return PROFILE_PLATFORMS[self.platform.index()]

    def _on_platform(self, _):
        self.handle.setPlaceholderText(_PLACEHOLDER.get(self.platform_key, "@kullanıcıadı ya da profil bağlantısı"))

    def _on_handle(self, text):
        p = detect(text) if "/" in text or "." in text else None
        if p and p.key in PROFILE_PLATFORMS:
            self.platform.set_index(PROFILE_PLATFORMS.index(p.key))

    def fetch(self):
        text = self.handle.text()
        self.go.setEnabled(False)
        self.busy.show()
        self.busy.set_value(None)
        self.status.setObjectName("Caption")
        self.status.setText("Aranıyor")
        self._restyle(self.status)
        key, cookies = self.platform_key, self.settings.cookies_browser
        run_async(lambda: profiles.fetch(text, key, cookies), self._fetched, self._fetch_failed, self)

    def _fetch_done(self):
        self.go.setEnabled(True)
        self.busy.hide()
        self.login.hide()

    def _login(self):
        if sign_in(self, self.platform_key, self.settings):
            self.fetch()

    def _fetch_failed(self, msg):
        self._fetch_done()
        self.status.setObjectName("Error")
        self.status.setText(msg)
        self._restyle(self.status)
        self.login.setVisible(profiles.LOGIN_HINT in msg)

    def _fetched(self, prof: profiles.Profile):
        self._fetch_done()
        self.profile = prof
        title = PLATFORMS[prof.platform].name + " · " + (prof.name or prof.handle)
        if prof.name and prof.handle and prof.handle.lower() not in prof.name.lower():
            title += f"  ({prof.handle})"
        self.status.setText("\n".join([title, *prof.notes]))
        self.opts = {"avatar": ImageOptions(), "banner": ImageOptions()}
        for kind, card in (("avatar", self.avatar_card), ("banner", self.banner_card)):
            asset = getattr(prof, kind)
            card.include.setChecked(bool(asset))
            card.include.setEnabled(bool(asset))
            if not asset:
                card.preview.set_image(None, "Bu hesapta kapak görseli bulunamadı." if kind == "banner"
                                       else "Profil fotoğrafı bulunamadı.")
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
        w, h, _ = image_info(self._asset(kind).data)
        return w, h

    def _select(self, kind: str):
        if not self._asset(kind):
            return
        self.current = kind
        self.avatar_card.set_highlight(kind == "avatar")
        self.banner_card.set_highlight(kind == "banner")
        o = self.opts[kind]
        self._syncing = True
        crops = _CROPS[kind]
        self.crop.set_items([t for t, _ in crops])
        self.crop.set_index([k for _, k in crops].index(o.crop), animate=False, emit=False)
        self.fmt.setCurrentIndex([k for _, k in _FORMATS].index(o.fmt))
        self.quality.setValue(o.quality)
        self.quality_value.setText(str(o.quality))
        self.lock.setChecked(o.keep_ratio)
        self._syncing = False
        self._sync_size()
        self._sync_quality()

    def _sync_size(self):
        tw, th = target_size(self._src_size(self.current), self.opts[self.current])
        self._syncing = True
        self.w.setValue(tw)
        self.h.setValue(th)
        self._syncing = False

    def _sync_quality(self):
        o = self.opts[self.current]
        src_ext = image_info(self._asset(self.current).data)[2]
        fmt = src_ext if o.fmt == "original" else o.fmt
        lossy = fmt in ("jpg", "webp") and o.crop != "circle"
        self.quality_field.setVisible(lossy)

    def _changed(self):
        self._generation[self.current] += 1
        self._debounce.start()

    def _on_size(self, axis: str, value: int):
        if self._syncing or not self.profile:
            return
        o = self.opts[self.current]
        if o.keep_ratio:
            o.width, o.height = (value, 0) if axis == "w" else (0, value)
        else:
            if axis == "w":
                o.width, o.height = value, o.height or self.h.value()
            else:
                o.width, o.height = o.width or self.w.value(), value
        self._sync_size()
        self._changed()

    def _on_lock(self, on: bool):
        self.lock.setIcon(icons.icon("lock" if on else "unlock", theme.TEXT if on else theme.TEXT_3))
        if self._syncing or not self.profile:
            return
        o = self.opts[self.current]
        o.keep_ratio = on
        if on:
            o.height = 0 if o.width else o.height
        self._sync_size()
        self._changed()

    def _reset_size(self):
        if not self.profile:
            return
        o = self.opts[self.current]
        o.width = o.height = 0
        self._sync_size()
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

    def _on_crop(self, index: int):
        if self._syncing or not self.profile:
            return
        self.opts[self.current].crop = _CROPS[self.current][index][1]
        self._sync_size()
        self._sync_quality()
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
            card.info.setText(dst if same else f"{src}  →  {dst}")

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
            self.saved.setText("Kaydedilecek görsel seçilmedi.")
            return
        folder = Path(self.settings.output_dir) / "Profiller"
        base = re.sub(r'[\\/:*?"<>|\s]+', "_", f"{prof.platform}_{prof.handle}").strip("_")

        def work():
            folder.mkdir(parents=True, exist_ok=True)
            written = []
            for kind, data, opts in jobs:
                out, ext = process_image(data, opts)
                path = folder / f"{base}_{_NAMES[kind]}.{ext}"
                n = 2
                while path.exists():
                    path = folder / f"{base}_{_NAMES[kind]} ({n}).{ext}"
                    n += 1
                path.write_bytes(out)
                written.append(path.name)
            return written

        self.save_btn.setEnabled(False)
        run_async(work, self._saved_ok, self._saved_err, self)

    def _saved_ok(self, names):
        self.save_btn.setEnabled(True)
        self.saved.setText("Kaydedildi: " + ", ".join(names))

    def _saved_err(self, msg):
        self.save_btn.setEnabled(True)
        self.saved.setText("Kaydedilemedi: " + msg)

    def _open_dir(self):
        folder = Path(self.settings.output_dir) / "Profiller"
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    @staticmethod
    def _restyle(w: QWidget):
        w.style().unpolish(w)
        w.style().polish(w)
