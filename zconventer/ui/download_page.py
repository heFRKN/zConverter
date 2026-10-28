import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (QComboBox, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout,
                               QWidget)

from ..core import downloader as dl
from ..core.media import parse_time
from ..core.platforms import detect
from ..core.settings import Settings
from . import icons, theme
from .jobs import Job, JobManager
from .widgets import (Badge, ElidedLabel, GlassCard, ProgressLine, Segmented, Toggle, field, hbox,
                      icon_button, label)

SUPPORTED = "YouTube · Spotify · SoundCloud · Instagram · TikTok · X · Reddit · Threads · Facebook"


def _open_path(path: str):
    QDesktopServices.openUrl(QUrl.fromLocalFile(path))


class JobRow(GlassCard):
    def __init__(self, job: Job, on_retry, on_remove):
        super().__init__(radius=14, padding=14, strength=0.9)
        self.job = job
        self.paths: list[str] = []
        self._on_retry = on_retry
        self._on_remove = on_remove
        p = detect(job.req.url)

        self.title = ElidedLabel(job.req.url)
        self.title.setObjectName("H2")
        self.title.setStyleSheet("font-size: 13px;")
        self.status = ElidedLabel("Sırada")
        self.status.setObjectName("Caption")
        self.bar = ProgressLine()

        self.btn_open = icon_button("folder", "Klasörde göster")
        self.btn_retry = icon_button("retry", "Tekrar dene")
        self.btn_x = icon_button("x", "İptal et")
        self.btn_open.hide()
        self.btn_retry.hide()
        self.btn_open.clicked.connect(self._open)
        self.btn_retry.clicked.connect(lambda: self._on_retry(self))
        self.btn_x.clicked.connect(self._x)

        mid = QVBoxLayout()
        mid.setSpacing(5)
        mid.addWidget(self.title)
        mid.addWidget(self.status)
        mid.addSpacing(2)
        mid.addWidget(self.bar)
        kind = "Ses" if job.req.mode == "audio" else "Video"
        meta = label(f"{kind} · {job.req.fmt.upper()}", "Caption")
        row = hbox(Badge(p.badge if p else "?"), 4, mid, 16, meta, self.btn_retry, self.btn_open, self.btn_x,
                   spacing=10, stretch=(mid,))
        self.layout().addLayout(row)

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

    def _done(self, paths):
        self.paths = paths
        n = len(paths)
        self.status.setText(f"Tamamlandı · {n} dosya" if n > 1 else "Tamamlandı · " + Path(paths[0]).name)
        self.bar.set_value(1.0)
        self.btn_open.show()
        self.btn_x.setToolTip("Listeden kaldır")

    def _failed(self, msg):
        self.status.setText(msg.replace("\n", "  "))
        self.status.setToolTip(msg)
        self.status.setStyleSheet(f"color: {theme.ERROR};")
        self.bar.set_value(1.0, error=True)
        self.btn_retry.show()
        self.btn_x.setToolTip("Listeden kaldır")

    def _cancelled(self):
        self.status.setText("İptal edildi")
        self.bar.set_value(0)
        self.btn_retry.show()
        self.btn_x.setToolTip("Listeden kaldır")

    def _open(self):
        if not self.paths:
            return
        target = self.paths[0]
        if os.path.exists(target):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(target)])
        else:
            _open_path(str(Path(target).parent))

    def _x(self):
        if self.job.state in ("queued", "running"):
            self.job.cancel()
        else:
            self._on_remove(self)


class DownloadPage(QWidget):
    def __init__(self, settings: Settings, manager: JobManager):
        super().__init__()
        self.settings = settings
        self.manager = manager
        self.rows: list[JobRow] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 36, 40, 28)
        root.setSpacing(6)
        root.addWidget(label("İndir", "H1"))
        root.addWidget(label("Bağlantıyı yapıştır, biçimi seç. Kırpma istersen indirmeden önce ayarla.", "Sub"))
        root.addSpacing(18)

        card = GlassCard(padding=22)
        root.addWidget(card)
        c = card.layout()
        c.setSpacing(18)

        # url row
        self.url = QLineEdit()
        self.url.setObjectName("Hero")
        self.url.setPlaceholderText("https://")
        self.url.setClearButtonEnabled(True)
        self.url.textChanged.connect(self._on_url)
        self.url.returnPressed.connect(self.start)
        self.chip = QLabel()
        self.chip.setObjectName("Chip")
        self.chip.hide()
        paste = QPushButton("  Yapıştır")
        paste.setIcon(icons.icon("paste", theme.TEXT_2))
        paste.setIconSize(QSize(16, 16))
        paste.setMinimumHeight(46)
        paste.setCursor(Qt.CursorShape.PointingHandCursor)
        paste.clicked.connect(self._paste)
        c.addLayout(hbox(self.url, paste, spacing=10, stretch=(self.url,)))
        c.addLayout(hbox(self.chip, label(SUPPORTED, "Caption"), None, spacing=10))

        # format row
        self.mode = Segmented(["Video", "Ses"])
        self.mode.changed.connect(self._on_mode)
        self.quality = QComboBox()
        self.quality.setMinimumWidth(140)
        self.fmt = QComboBox()
        self.fmt.setMinimumWidth(110)
        self.fmt.currentTextChanged.connect(self._on_fmt)
        c.addLayout(hbox(field("Tür", self.mode), field("Kalite", self.quality), field("Biçim", self.fmt),
                         None, spacing=16))

        # trim + extras
        self.trim = Toggle("Kırp")
        self.trim.toggled.connect(self._on_trim)
        self.start_at = QLineEdit()
        self.start_at.setPlaceholderText("0:00")
        self.end_at = QLineEdit()
        self.end_at.setPlaceholderText("son")
        for w in (self.start_at, self.end_at):
            w.setFixedWidth(92)
            w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            w.setEnabled(False)
            w.setToolTip("Biçim: 90, 1:30 ya da 1:02:30")
        arrow = label("→", "Caption")
        self.playlist = Toggle("Tüm oynatma listesi")
        self.cover = Toggle("Kapak ve etiketler", checked=True)
        c.addLayout(hbox(self.trim, 6, self.start_at, arrow, self.end_at, 18, self.playlist, 18,
                         self.cover, None, spacing=8))

        # footer
        self.hint = label("", "Caption")
        self.error = label("", "Error")
        self.go = QPushButton("İndir")
        self.go.setObjectName("Primary")
        self.go.setIcon(icons.icon("download", "#FFFFFF"))
        self.go.setIconSize(QSize(17, 17))
        self.go.setCursor(Qt.CursorShape.PointingHandCursor)
        self.go.clicked.connect(self.start)
        msgs = QVBoxLayout()
        msgs.setSpacing(2)
        msgs.addWidget(self.hint)
        msgs.addWidget(self.error)
        c.addLayout(hbox(msgs, None, self.go))

        # queue
        root.addSpacing(22)
        clear = QPushButton("Bitenleri temizle")
        clear.setObjectName("Link")
        clear.setCursor(Qt.CursorShape.PointingHandCursor)
        clear.clicked.connect(self._clear_finished)
        open_dir = QPushButton("Klasörü aç")
        open_dir.setObjectName("Link")
        open_dir.setCursor(Qt.CursorShape.PointingHandCursor)
        open_dir.clicked.connect(self._open_output)
        root.addLayout(hbox(label("KUYRUK", "Section"), None, open_dir, 14, clear))
        root.addSpacing(8)

        self.list_host = QWidget()
        self.list_lay = QVBoxLayout(self.list_host)
        self.list_lay.setContentsMargins(0, 0, 6, 0)
        self.list_lay.setSpacing(8)
        self.empty = label("Henüz bir şey yok. İndirdiklerin burada görünecek.", "Caption")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setMinimumHeight(80)
        self.list_lay.addWidget(self.empty)
        self.list_lay.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.list_host)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root.addWidget(scroll, 1)

        manager.added.connect(self._add_row)
        self._on_mode(0)
        self._on_url("")

    # ------------------------------------------------------------ state

    def set_url(self, text: str):
        self.url.setText(text.strip())
        self.url.setFocus()

    def _paste(self):
        self.set_url(QGuiApplication.clipboard().text())

    def _on_url(self, text):
        self.error.setText("")
        p = detect(text) if text.strip() else None
        self.chip.setVisible(bool(p))
        if p:
            self.chip.setText(p.name)
        audio_only = bool(p and p.audio_only)
        self.mode.set_disabled(0, audio_only)
        if audio_only and self.mode.index() == 0:
            self.mode.set_index(1)
        if p and p.key == "spotify":
            self.hint.setText("Spotify DRM'li olduğu için ses doğrudan indirilmez; parça bilgisi okunup "
                              "YouTube'daki karşılığı bulunur.")
        elif p and p.key in ("instagram", "facebook", "threads"):
            self.hint.setText("Gizli ya da giriş isteyen gönderiler için Ayarlar → Tarayıcı oturumu.")
        else:
            self.hint.setText("")

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
        lossless = fmt in ("flac", "wav")
        self.quality.setEnabled(not (audio and lossless))
        self.cover.setEnabled(fmt in dl.COVER_FORMATS)
        self.cover.setToolTip("" if fmt in dl.COVER_FORMATS else "Kapak gömme yalnızca MP3 ve M4A için.")

    def _on_trim(self, on):
        self.start_at.setEnabled(on)
        self.end_at.setEnabled(on)
        if on:
            self.start_at.setFocus()

    # ------------------------------------------------------------ actions

    def start(self):
        url = self.url.text().strip()
        if not url:
            self.error.setText("Önce bir bağlantı yapıştır.")
            return
        if not detect(url):
            self.error.setText("Bu bağlantı desteklenen platformlardan birine ait değil.")
            return
        start = end = None
        if self.trim.isChecked():
            try:
                start = parse_time(self.start_at.text())
                end = parse_time(self.end_at.text())
            except ValueError:
                self.error.setText("Süre biçimi geçersiz. Örnek: 1:30 ya da 0:45")
                return
            if start is not None and end is not None and end <= start:
                self.error.setText("Bitiş, başlangıçtan sonra olmalı.")
                return
            if start == 0:
                start = None
        req = dl.Request(
            url=url,
            mode="audio" if self.mode.index() == 1 else "video",
            quality=self.quality.currentData() or "best",
            fmt=self.fmt.currentText(),
            start=start,
            end=end,
            playlist=self.playlist.isChecked(),
            cover=self.cover.isChecked(),
            output_dir=self.settings.output_dir,
            cookies_browser=self.settings.cookies_browser,
        )
        self.manager.submit(req)
        self.url.clear()
        self.error.setText("")

    def _add_row(self, job: Job):
        self.empty.hide()
        row = JobRow(job, self._retry, self._remove)
        self.rows.insert(0, row)
        self.list_lay.insertWidget(0, row)

    def _retry(self, row: JobRow):
        self._remove(row)
        self.manager.submit(row.job.req)

    def _remove(self, row: JobRow):
        if row in self.rows:
            self.rows.remove(row)
        row.setParent(None)
        row.deleteLater()
        self.empty.setVisible(not self.rows)

    def _clear_finished(self):
        for row in [r for r in self.rows if r.job.state in ("done", "cancelled", "failed")]:
            self._remove(row)

    def _open_output(self):
        Path(self.settings.output_dir).mkdir(parents=True, exist_ok=True)
        _open_path(self.settings.output_dir)
