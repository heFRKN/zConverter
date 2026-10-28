from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QPushButton, QScrollArea, QVBoxLayout, QWidget

from .. import AUTHOR, REPO_URL, __version__
from ..core import accounts
from ..core.paths import js_runtime
from ..core.settings import Settings
from ..i18n import language, restart_app, t
from .jobs import JobManager
from .location import change_folder, open_folder
from .widgets import Card, ElidedLabel, Segmented, Toggle, hbox, label

def _pkg_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "?"


def _card(title: str, *rows) -> Card:
    card = Card(padding=20)
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
        root.addWidget(label(t("Ayarlar"), "H1"))
        root.addWidget(label(t("Her şey bu bilgisayarda kalır. Uygulama hiçbir veriyi bize göndermez."), "Sub"))
        root.addSpacing(18)

        # language
        self.language = Segmented(["Türkçe", "English"], height=34)
        self.language.set_index(0 if language() == "tr" else 1, animate=False, emit=False)
        self.language.changed.connect(self._on_language)
        self.restart = QPushButton(t("Yeniden başlat"))
        self.restart.setObjectName("Primary")
        self.restart.clicked.connect(restart_app)
        self.restart.hide()
        root.addWidget(_card(t("Dil") + " / Language", hbox(self.language, 12, self.restart, None)))
        root.addSpacing(12)

        # output folder
        self.path = ElidedLabel(settings.output_dir)
        self.path.setObjectName("Muted")
        change = QPushButton(t("Değiştir"))
        change.clicked.connect(self._pick_dir)
        open_btn = QPushButton(t("Aç"))
        open_btn.clicked.connect(self._open_dir)
        root.addWidget(_card(t("Kayıt yeri"), hbox(self.path, change, open_btn, stretch=(self.path,))))
        root.addSpacing(12)

        # accounts
        self.account_rows = {}
        rows = []
        for key, (name, *_rest) in accounts.PLATFORMS.items():
            status = label("", "Caption")
            btn = QPushButton()
            btn.setFixedWidth(110)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self._toggle_account(k))
            n = label(name, "Muted")
            n.setFixedWidth(120)
            self.account_rows[key] = (status, btn)
            rows.append(hbox(n, status, None, btn))
        self.firefox = Toggle(t("Firefox'taki açık oturumu kullan"), checked=settings.cookies_browser == "firefox")
        self.firefox.toggled.connect(self._on_firefox)
        root.addWidget(_card(
            t("Hesaplar"),
            label(t("Gizli, yaş sınırlı ya da giriş isteyen içerikler (Reddit videoları gibi) için hesabına giriş yap. "
                    "Giriş, platformun kendi sayfasında uygulamanın içinde yapılır; şifren uygulamaya geçmez. "
                    "Oturum bu bilgisayarda Windows şifrelemesiyle saklanır ve sadece o platforma gönderilir. "
                    "Sadece kendi hesabını kullan."), "Muted", wrap=True),
            *rows,
            self.firefox,
        ))
        self._refresh_accounts()
        root.addSpacing(12)

        # parallel
        self.parallel = Segmented(["1", "2", "3", "4"], height=34)
        self.parallel.set_index(max(0, min(3, settings.parallel - 1)), animate=False, emit=False)
        self.parallel.changed.connect(self._on_parallel)
        root.addWidget(_card(t("Aynı anda indirme"), hbox(self.parallel, None)))
        root.addSpacing(12)

        # components
        rt = js_runtime()
        js_text = (t("{name} bulundu", name=rt) if rt else
                   t("Bulunamadı. YouTube'da bazı kaliteler eksik kalabilir. Kurmak için terminalde: ")
                   + "winget install DenoLand.Deno")

        gh = QPushButton(t("GitHub'da aç"))
        gh.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))
        root.addWidget(_card(
            t("Hakkında"),
            label(t("zConverter {version} · MIT Lisansı · © 2026 {author}", version=__version__, author=AUTHOR), "Muted"),
            label(t("Bağımsız, açık kaynaklı bir projedir. Adı geçen platformların hiçbiriyle bağlantılı değildir, "
                    "onlar tarafından desteklenmez veya onaylanmaz."), "Caption", wrap=True),
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
        if change_folder(self, self.settings):
            self.path.setText(self.settings.output_dir)

    def _open_dir(self):
        open_folder(self.settings.output_dir)

    def _refresh_accounts(self):
        for key, (status, btn) in self.account_rows.items():
            on = accounts.signed_in(key)
            status.setText(t("Bağlı") if on else t("Bağlı değil"))
            btn.setText(t("Çıkış yap") if on else t("Giriş yap"))

    def _toggle_account(self, key: str):
        if accounts.signed_in(key):
            accounts.sign_out(key)
        else:
            from .login_dialog import LoginDialog
            LoginDialog(key, self).exec()
        self._refresh_accounts()

    def showEvent(self, e):
        super().showEvent(e)
        self.path.setText(self.settings.output_dir)
        self._refresh_accounts()  # a login from the download page may have happened meanwhile

    def _on_language(self, index: int):
        self.settings.language = "tr" if index == 0 else "en"
        self.settings.save()
        self.restart.setVisible(self.settings.language != language())

    def _on_firefox(self, on: bool):
        self.settings.cookies_browser = "firefox" if on else ""
        self.settings.save()

    def _on_parallel(self, index: int):
        self.settings.parallel = index + 1
        self.settings.save()
        self.manager.set_parallel(index + 1)
