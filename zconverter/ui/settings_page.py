from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QComboBox, QFileDialog, QPushButton, QScrollArea, QVBoxLayout, QWidget

from .. import AUTHOR, REPO_URL, __version__
from ..core.paths import js_runtime
from ..core.settings import Settings
from .jobs import JobManager
from .widgets import ElidedLabel, GlassCard, Segmented, hbox, label

BROWSERS = [("Kapalı", ""), ("Firefox", "firefox"), ("Edge", "edge"), ("Chrome", "chrome"),
            ("Brave", "brave"), ("Opera", "opera"), ("Vivaldi", "vivaldi")]


def _pkg_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "?"


def _card(title: str, *rows) -> GlassCard:
    card = GlassCard(padding=20)
    card.layout().setSpacing(10)
    card.layout().addWidget(label(title, "H2"))
    for row in rows:
        if isinstance(row, QWidget):
            card.layout().addWidget(row)
        else:
            card.layout().addLayout(row)
    return card


class SettingsPage(QWidget):
    def __init__(self, settings: Settings, manager: JobManager):
        super().__init__()
        self.settings = settings
        self.manager = manager

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
        root.addWidget(label("Ayarlar", "H1"))
        root.addWidget(label("Her şey bu bilgisayarda kalır. Uygulama hiçbir veriyi bize göndermez.", "Sub"))
        root.addSpacing(18)

        # output folder
        self.path = ElidedLabel(settings.output_dir)
        self.path.setObjectName("Muted")
        change = QPushButton("Değiştir")
        change.clicked.connect(self._pick_dir)
        open_btn = QPushButton("Aç")
        open_btn.clicked.connect(self._open_dir)
        root.addWidget(_card("Kayıt yeri", hbox(self.path, change, open_btn, stretch=(self.path,))))
        root.addSpacing(12)

        # browser session
        self.browser = QComboBox()
        self.browser.setMinimumWidth(160)
        for text, key in BROWSERS:
            self.browser.addItem(text, key)
        keys = [k for _, k in BROWSERS]
        self.browser.setCurrentIndex(keys.index(settings.cookies_browser) if settings.cookies_browser in keys else 0)
        self.browser.currentIndexChanged.connect(self._on_browser)
        root.addWidget(_card(
            "Tarayıcı oturumu",
            label("Gizli, yaş sınırlı ya da giriş isteyen içerikler ve Instagram / Reddit / Facebook profilleri "
                  "için, giriş yaptığın tarayıcının çerezleri kullanılır. Çerezler yalnızca bu bilgisayarda "
                  "okunur, kaydedilmez ve sadece ilgili platformun kendisine gönderilir. Sadece kendi hesabını "
                  "kullan.", "Muted", wrap=True),
            label("Chrome ve Edge yeni sürümlerde çerezleri şifreler; okunamazsa Firefox önerilir. "
                  "Okuma sırasında tarayıcının kapalı olması gerekebilir.", "Caption", wrap=True),
            hbox(self.browser, None),
        ))
        root.addSpacing(12)

        # parallel
        self.parallel = Segmented(["1", "2", "3", "4"], height=34)
        self.parallel.set_index(max(0, min(3, settings.parallel - 1)), animate=False, emit=False)
        self.parallel.changed.connect(self._on_parallel)
        root.addWidget(_card("Aynı anda indirme", hbox(self.parallel, None)))
        root.addSpacing(12)

        # components
        rt = js_runtime()
        js_text = (f"{rt} bulundu" if rt else
                   "Bulunamadı. YouTube'da bazı kaliteler eksik kalabilir. Kurmak için terminalde: "
                   "winget install DenoLand.Deno")
        root.addWidget(_card(
            "Bileşenler",
            self._row("yt-dlp", _pkg_version("yt-dlp")),
            self._row("FFmpeg", "dahili (imageio-ffmpeg " + _pkg_version("imageio-ffmpeg") + ")"),
            self._row("JavaScript çalışma ortamı", js_text),
        ))
        root.addSpacing(12)

        gh = QPushButton("GitHub'da aç")
        gh.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))
        root.addWidget(_card(
            "Hakkında",
            label(f"zConverter {__version__} · MIT Lisansı · © 2026 {AUTHOR}", "Muted"),
            label("Bağımsız, açık kaynaklı bir projedir. Adı geçen platformların hiçbiriyle bağlantılı değildir, "
                  "onlar tarafından desteklenmez veya onaylanmaz.", "Caption", wrap=True),
            hbox(gh, None),
        ))
        root.addStretch(1)

    @staticmethod
    def _row(name: str, value: str):
        k = label(name, "Muted")
        k.setFixedWidth(200)
        v = label(value, wrap=True)
        v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return hbox(k, v, spacing=12, stretch=(v,))

    def _pick_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Kayıt yeri", self.settings.output_dir)
        if path:
            self.settings.output_dir = str(Path(path))
            self.settings.save()
            self.path.setText(self.settings.output_dir)

    def _open_dir(self):
        Path(self.settings.output_dir).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.settings.output_dir))

    def _on_browser(self, index: int):
        self.settings.cookies_browser = BROWSERS[index][1]
        self.settings.save()

    def _on_parallel(self, index: int):
        self.settings.parallel = index + 1
        self.settings.save()
        self.manager.set_parallel(index + 1)
