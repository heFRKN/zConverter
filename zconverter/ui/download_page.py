import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication, QPixmap
from PySide6.QtWidgets import (QComboBox, QLineEdit, QPushButton, QScrollArea, QVBoxLayout,
                               QWidget)

from ..core import downloader as dl
from ..core import probe
from ..core.downloader import humanize, needs_login
from ..core.media import format_time
from ..core.net import session
from ..core.platforms import PLATFORMS, detect, normalize_url
from ..core.settings import Settings
from . import icons, theme
from .jobs import Job, JobManager, run_async
from .login_dialog import sign_in
from .trim_editor import TrimEditor
from .widgets import (Badge, Card, ElidedLabel, ProgressLine, Segmented, Thumb, Toggle, field, hbox,
                      icon_button, label)

SUPPORTED = "YouTube · Spotify · SoundCloud · Instagram · TikTok · X · Reddit · Threads · Facebook"


def _looks_like_list(url: str) -> bool:
    return any(k in url for k in ("list=", "/playlist", "/sets/", "/album/"))


class JobRow(Card):
    def __init__(self, job: Job, page: "DownloadPage"):
        super().__init__(radius=10, padding=12)
        self.job = job
        self.page = page
        self.paths: list[str] = []
        p = detect(job.req.url)

        self.title = ElidedLabel(job.req.url)
        self.title.setStyleSheet("font-weight: 600;")
        self.status = ElidedLabel("Sırada")
        self.status.setObjectName("Caption")
        self.bar = ProgressLine()

        self.btn_auth = QPushButton(" Giriş yap")
        self.btn_auth.setIcon(icons.icon("key", theme.TEXT_2))
        self.btn_auth.setIconSize(QSize(15, 15))
        self.btn_auth.setMinimumHeight(30)
        self.btn_open = icon_button("folder", "Klasörde göster")
        self.btn_retry = icon_button("retry", "Tekrar dene")
        self.btn_x = icon_button("x", "İptal et")
        for b in (self.btn_auth, self.btn_open, self.btn_retry):
            b.hide()
        self.btn_auth.clicked.connect(self._auth)
        self.btn_open.clicked.connect(self._open)
        self.btn_retry.clicked.connect(lambda: page.retry(self))
        self.btn_x.clicked.connect(self._x)

        mid = QVBoxLayout()
        mid.setSpacing(4)
        mid.addWidget(self.title)
        mid.addWidget(self.status)
        mid.addSpacing(3)
        mid.addWidget(self.bar)
        r = job.req
        kind = "Ses" if r.mode == "audio" else "Video"
        extra = ""
        if r.trimming:
            extra = f" · {format_time(r.start or 0)}–{format_time(r.end) if r.end is not None else 'son'}"
        meta = label(f"{kind} · {r.fmt.upper()}{extra}", "Caption")
        self.layout().addLayout(hbox(Badge(p.badge if p else "?"), 4, mid, 14, meta, self.btn_auth,
                                     self.btn_retry, self.btn_open, self.btn_x, spacing=8, stretch=(mid,)))

        job.title.connect(self.title.setText)
        job.status.connect(self._status)
        job.progress.connect(self._progress)
        job.done.connect(self._done)
        job.failed.connect(self._failed)
        job.cancelled.connect(self._cancelled)

    def _status(self, text):
        self.status.setText(text)
        self.bar.set_value(None)

    def _progress(self, value, text):
        self.status.setText(text)
        self.bar.set_value(value)

    def _finished(self):
        self.btn_x.setToolTip("Listeden kaldır")

    def _done(self, paths):
        self.paths = paths
        n = len(paths)
        self.status.setText(f"Tamamlandı · {n} dosya" if n > 1 else "Tamamlandı · " + Path(paths[0]).name)
        self.bar.set_value(1.0)
        self.btn_open.show()
        self._finished()

    def _failed(self, msg, login):
        self.status.setText(msg)
        self.status.setToolTip(msg)
        self.status.setStyleSheet(f"color: {theme.ERROR};")
        self.bar.set_value(1.0, error=True)
        self.btn_retry.show()
        self.btn_auth.setVisible(login)
        self._finished()

    def _cancelled(self):
        self.status.setText("İptal edildi")
        self.bar.set_value(0)
        self.btn_retry.show()
        self._finished()

    def _auth(self):
        p = detect(self.job.req.url)
        if p and sign_in(self, p.key, self.page.settings):
            self.page.retry(self, with_session=True)

    def _open(self):
        if not self.paths:
            return
        target = self.paths[0]
        if os.path.exists(target):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(target)])
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(target).parent)))

    def _x(self):
        if self.job.state in ("queued", "running"):
            self.job.cancel()
        else:
            self.page.remove(self)


class DownloadPage(QWidget):
    def __init__(self, settings: Settings, manager: JobManager):
        super().__init__()
        self.settings = settings
        self.manager = manager
        self.rows: list[JobRow] = []
        self.info: probe.MediaInfo | None = None
        self._probe_gen = 0
        self._forced_audio = False

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
        root.addWidget(label("İndir", "H1"))
        root.addWidget(label("Bağlantıyı yapıştır. Önizleme gelince biçimi seç, istersen kırp.", "Sub"))
        root.addSpacing(14)

        # ---------------- link
        link = Card(padding=16)
        link.layout().setSpacing(10)
        root.addWidget(link)
        self.url = QLineEdit()
        self.url.setObjectName("Hero")
        self.url.setPlaceholderText("Bağlantıyı buraya yapıştır")
        self.url.setClearButtonEnabled(True)
        self.url.textChanged.connect(self._on_url)
        self.url.returnPressed.connect(self._probe_now)
        paste = QPushButton(" Yapıştır")
        paste.setIcon(icons.icon("paste", theme.TEXT_2))
        paste.setIconSize(QSize(15, 15))
        paste.setMinimumHeight(42)
        paste.setCursor(Qt.CursorShape.PointingHandCursor)
        paste.clicked.connect(self._paste)
        link.layout().addLayout(hbox(self.url, paste, stretch=(self.url,)))
        self.chip = label("", "Chip")
        self.chip.hide()
        self.link_status = label(SUPPORTED, "Caption")
        link.layout().addLayout(hbox(self.chip, self.link_status, None, spacing=8))
        self.busy = ProgressLine()
        self.busy.hide()
        link.layout().addWidget(self.busy)

        # ---------------- preview + options + trim
        self.card = Card(padding=20)
        self.card.hide()
        root.addSpacing(10)
        root.addWidget(self.card)
        c = self.card.layout()
        c.setSpacing(16)

        self.thumb = Thumb(176, 99)
        self.title = label("", "H2", wrap=True)
        self.meta = label("", "Caption", wrap=True)
        self.note = label("", "Caption", wrap=True)
        self.error = label("", "Error", wrap=True)
        self.auth = QPushButton(" Giriş yap ve tekrar dene")
        self.auth.setIcon(icons.icon("key", theme.TEXT_2))
        self.auth.setIconSize(QSize(15, 15))
        self.auth.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auth.clicked.connect(self._auth)
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        info_col.addWidget(self.title)
        info_col.addWidget(self.meta)
        info_col.addWidget(self.note)
        info_col.addWidget(self.error)
        info_col.addLayout(hbox(self.auth, None))
        info_col.addStretch(1)
        c.addLayout(hbox(self.thumb, 6, info_col, spacing=12, stretch=(info_col,)))

        self.mode = Segmented(["Video", "Ses"])
        self.mode.changed.connect(self._on_mode)
        self.quality = QComboBox()
        self.quality.setMinimumWidth(130)
        self.fmt = QComboBox()
        self.fmt.setMinimumWidth(96)
        self.fmt.currentTextChanged.connect(self._on_fmt)
        self.cover = Toggle("Kapak ve etiketler", checked=True)
        self.playlist = Toggle("Tüm listeyi indir")
        self.playlist.toggled.connect(lambda _: self._probe_now())
        toggles = QVBoxLayout()
        toggles.setSpacing(8)
        toggles.addSpacing(18)
        toggles.addWidget(self.cover)
        toggles.addWidget(self.playlist)
        c.addLayout(hbox(field("Tür", self.mode), field("Kalite", self.quality), field("Biçim", self.fmt),
                         12, toggles, None, spacing=14))

        self.trim_box = QWidget()
        tb = QVBoxLayout(self.trim_box)
        tb.setContentsMargins(0, 4, 0, 0)
        tb.setSpacing(10)
        tb.addLayout(hbox(label("KIRP", "Section"),
                          label("Tutamakları sürükle ya da zamanı yaz. Seçili aralık indirilir.", "Caption"),
                          None, spacing=10))
        self.editor = TrimEditor()
        tb.addWidget(self.editor)
        c.addWidget(self.trim_box)

        self.go = QPushButton("İndir")
        self.go.setObjectName("Primary")
        self.go.setIcon(icons.icon("download", "#FFFFFF"))
        self.go.setIconSize(QSize(16, 16))
        self.go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.go.clicked.connect(self.start)
        self.save_to = label("", "Caption")
        c.addLayout(hbox(self.save_to, None, self.go))

        # ---------------- queue
        root.addSpacing(20)
        clear = QPushButton("Bitenleri temizle")
        clear.setObjectName("Link")
        clear.setCursor(Qt.CursorShape.PointingHandCursor)
        clear.clicked.connect(self._clear_finished)
        open_dir = QPushButton("Klasörü aç")
        open_dir.setObjectName("Link")
        open_dir.setCursor(Qt.CursorShape.PointingHandCursor)
        open_dir.clicked.connect(self._open_output)
        root.addLayout(hbox(label("KUYRUK", "Section"), None, open_dir, 14, clear))
        root.addSpacing(6)
        self.list_lay = QVBoxLayout()
        self.list_lay.setSpacing(6)
        self.empty = label("Henüz bir şey yok. İndirdiklerin burada görünecek.", "Caption")
        self.empty.setMinimumHeight(48)
        self.list_lay.addWidget(self.empty)
        root.addLayout(self.list_lay)
        root.addStretch(1)

        self._timer = QTimer(self, singleShot=True, interval=500)
        self._timer.timeout.connect(self._probe_now)
        manager.added.connect(self._add_row)
        self._on_mode(0)

    # ------------------------------------------------------------ link → preview

    def set_url(self, text: str):
        self.url.setText(text.strip())
        self._probe_now()

    def _paste(self):
        self.set_url(QGuiApplication.clipboard().text())

    def _on_url(self, text):
        p = detect(text) if text.strip() else None
        self.chip.setVisible(bool(p))
        self.chip.setText(p.name if p else "")
        self.link_status.setText(SUPPORTED if not text.strip() else ("" if p else
                                 "Bu bağlantı desteklenen platformlardan birine ait değil."))
        audio_only = bool(p and p.audio_only)
        self.mode.set_disabled(0, audio_only)
        if audio_only and self.mode.index() == 0:
            self.mode.set_index(1)
            self._forced_audio = True
        elif p and not audio_only and self._forced_audio:
            self._forced_audio = False  # only undo what the platform forced, not the user's choice
            self.mode.set_index(0)
        if not p:
            self._probe_gen += 1
            self.busy.hide()
            self.card.hide()
            self.editor.stop()
            return
        self._timer.start()

    def _probe_now(self):
        url = self.url.text().strip()
        p = detect(url)
        if not p:
            return
        self._timer.stop()
        self._probe_gen += 1
        gen = self._probe_gen
        self.busy.show()
        self.busy.set_value(None)
        self.link_status.setText("Bilgiler alınıyor")
        self.playlist.setVisible(_looks_like_list(url))
        cookies, playlist = self.settings.cookies_browser, self.playlist.isChecked()
        run_async(lambda: probe.probe(url, cookies, playlist),
                  lambda info: gen == self._probe_gen and self._probed(info),
                  lambda err: gen == self._probe_gen and self._probe_failed(url, err), self)

    def _probed(self, info: probe.MediaInfo):
        self.info = info
        self.busy.hide()
        self.link_status.setText("")
        self.error.hide()
        self.auth.hide()
        self.title.setText(info.title or "Başlıksız")
        meta = [x for x in (info.uploader, PLATFORMS[info.platform].name if info.platform in PLATFORMS else "")
                if x]
        if info.count > 1:
            meta.insert(0, f"{info.count} öğe")
            self.playlist.setVisible(True)
        if info.duration:
            meta.insert(0, format_time(info.duration))
        self.meta.setText(" · ".join(meta))
        self.note.setText(info.note)
        self.note.setVisible(bool(info.note))
        self._load_thumb(info.thumbnail)
        self.trim_box.setVisible(info.trimmable)
        if info.trimmable:
            self.editor.load(info)
        else:
            self.editor.stop()
        self._show_card()

    def _probe_failed(self, url: str, err: str):
        self.info = None
        self.busy.hide()
        self.link_status.setText("")
        self.title.setText("Önizleme alınamadı")
        self.meta.setText(url)
        self.note.hide()
        self.error.setText(humanize(err))
        self.error.show()
        self.auth.setVisible(needs_login(err))
        self.thumb.set_pixmap(None, "Önizleme yok")
        self.trim_box.hide()
        self.editor.stop()
        self._show_card()

    def _show_card(self):
        self.save_to.setText("Kayıt yeri: " + self.settings.output_dir)
        self.card.show()

    def _load_thumb(self, url: str | None):
        self.thumb.set_pixmap(None, "")
        if not url:
            return
        gen = self._probe_gen

        def ok(data):
            if gen == self._probe_gen:
                px = QPixmap()
                px.loadFromData(data)
                self.thumb.set_pixmap(px)

        run_async(lambda: session().get(url, timeout=15).content, ok, lambda _: None, self)

    def _auth(self):
        p = detect(self.url.text())
        if p and sign_in(self, p.key, self.settings):
            self._probe_now()

    # ------------------------------------------------------------ options

    def _on_mode(self, index):
        audio = index == 1
        self.quality.clear()
        for key, text in (dl.AUDIO_QUALITIES if audio else dl.VIDEO_QUALITIES):
            self.quality.addItem(text, key)
        self.fmt.clear()
        self.fmt.addItems(dl.AUDIO_FORMATS if audio else dl.VIDEO_FORMATS)
        self.cover.setVisible(audio)
        self._on_fmt(self.fmt.currentText())

    def _on_fmt(self, fmt):
        audio = self.mode.index() == 1
        self.quality.setEnabled(not (audio and fmt in ("flac", "wav")))
        self.cover.setEnabled(fmt in dl.COVER_FORMATS)
        self.cover.setToolTip("" if fmt in dl.COVER_FORMATS else "Kapak gömme yalnızca MP3 ve M4A için.")

    # ------------------------------------------------------------ actions

    def start(self):
        url = self.url.text().strip()
        if not detect(url):
            return
        start = end = None
        if self.info and self.info.trimmable and self.trim_box.isVisible():
            start, end = self.editor.range()
        playlist = bool(self.info and self.info.count > 1) or (self.playlist.isVisible() and self.playlist.isChecked())
        req = dl.Request(
            url=normalize_url(url),
            mode="audio" if self.mode.index() == 1 else "video",
            quality=self.quality.currentData() or "best",
            fmt=self.fmt.currentText(),
            start=start,
            end=end,
            playlist=playlist,
            cover=self.cover.isChecked(),
            output_dir=self.settings.output_dir,
            cookies_browser=self.settings.cookies_browser,
        )
        self.manager.submit(req)
        self.editor.stop()
        self.url.clear()

    def _add_row(self, job: Job):
        self.empty.hide()
        row = JobRow(job, self)
        self.rows.insert(0, row)
        self.list_lay.insertWidget(0, row)

    def retry(self, row: JobRow, with_session: bool = False):
        req = row.job.req
        if with_session:
            req.cookies_browser = self.settings.cookies_browser
        self.remove(row)
        self.manager.submit(req)

    def remove(self, row: JobRow):
        if row in self.rows:
            self.rows.remove(row)
        row.setParent(None)
        row.deleteLater()
        self.empty.setVisible(not self.rows)

    def _clear_finished(self):
        for row in [r for r in self.rows if r.job.state in ("done", "cancelled", "failed")]:
            self.remove(row)

    def _open_output(self):
        Path(self.settings.output_dir).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.settings.output_dir))
