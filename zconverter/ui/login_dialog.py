"""In-app sign in. The user logs in on the platform's own page inside an embedded browser;
the password never touches the app, only the resulting session cookies are kept (encrypted)."""

from PySide6.QtCore import QDateTime, Qt, QTimer, QUrl
from PySide6.QtNetwork import QNetworkCookie
from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QWidget

from ..core import accounts
from ..core.settings import Settings
from .widgets import hbox, label


class LoginDialog(QDialog):
    def __init__(self, platform: str, parent=None):
        super().__init__(parent)
        from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
        from PySide6.QtWebEngineWidgets import QWebEngineView

        self.platform = platform
        name, url, domains, _ = accounts.PLATFORMS[platform]
        self.setWindowTitle(f"{name} girişi")
        self.resize(1000, 760)
        self._cookies: dict[tuple, dict] = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        bar = QWidget()
        bar.setObjectName("Sidebar")
        self.status = label("Giriş yapınca pencere kendiliğinden kapanır.", "Caption")
        done = QPushButton("Bitti")
        done.setObjectName("Primary")
        done.setCursor(Qt.CursorShape.PointingHandCursor)
        done.clicked.connect(self._finish)
        cancel = QPushButton("Vazgeç")
        cancel.clicked.connect(self.reject)
        info = QVBoxLayout()
        info.setSpacing(2)
        info.addWidget(label(f"{name} hesabına giriş", "H2"))
        info.addWidget(label(f"Giriş doğrudan {domains[0]} sayfasında yapılır; şifren uygulamaya geçmez. "
                             "Oturum bu bilgisayarda şifreli saklanır.", "Caption"))
        bar.setLayout(hbox(info, None, self.status, 12, cancel, done, margins=(18, 12, 18, 12)))
        lay.addWidget(bar)

        # private, in-memory browser profile: nothing is written by the engine itself
        self.profile = QWebEngineProfile(self)
        store = self.profile.cookieStore()
        store.cookieAdded.connect(self._added)
        store.cookieRemoved.connect(self._removed)
        saved = accounts.load(platform)
        # a stale session is preloaded too; only a *new* session cookie means the user just signed in
        self._old_marker = {c["value"] for c in saved if accounts.is_signed_in_cookie(platform, c["name"])}
        for c in saved:
            store.setCookie(self._to_qt(c))
        self._popups = []

        dialog = self

        class Page(QWebEnginePage):
            # "Continue with Google / Apple" open a popup; give it a window on the same private profile
            def createWindow(self, _type):
                view = QWebEngineView()
                page = Page(dialog.profile, view)
                view.setPage(page)
                view.setWindowTitle(dialog.windowTitle())
                view.resize(520, 680)
                page.windowCloseRequested.connect(view.close)
                dialog._popups.append(view)
                view.show()
                return page

        self.view = QWebEngineView(self)
        self.view.setPage(Page(self.profile, self.view))
        self.view.load(QUrl(url))
        lay.addWidget(self.view, 1)
        self.finished.connect(lambda _: [v.close() for v in self._popups])

    @staticmethod
    def _to_qt(c: dict) -> QNetworkCookie:
        qc = QNetworkCookie(c["name"].encode(), c["value"].encode())
        qc.setDomain(c["domain"])
        qc.setPath(c.get("path") or "/")
        qc.setSecure(bool(c.get("secure")))
        qc.setHttpOnly(bool(c.get("httponly")))
        if c.get("expires"):
            qc.setExpirationDate(QDateTime.fromSecsSinceEpoch(int(c["expires"])))
        return qc

    @staticmethod
    def _from_qt(qc: QNetworkCookie) -> dict:
        exp = qc.expirationDate()
        return {
            "name": bytes(qc.name()).decode("utf-8", "replace"),
            "value": bytes(qc.value()).decode("utf-8", "replace"),
            "domain": qc.domain(),
            "path": qc.path() or "/",
            "secure": qc.isSecure(),
            "httponly": qc.isHttpOnly(),
            "expires": exp.toSecsSinceEpoch() if exp.isValid() else None,
        }

    def _added(self, qc: QNetworkCookie):
        c = self._from_qt(qc)
        if not accounts.domain_matches(c["domain"], self.platform):
            return
        self._cookies[(c["domain"], c["path"], c["name"])] = c
        if (accounts.is_signed_in_cookie(self.platform, c["name"]) and c["value"]
                and c["value"] not in self._old_marker):
            self.status.setText("Giriş yapıldı")
            QTimer.singleShot(1200, self._finish)

    def _removed(self, qc: QNetworkCookie):
        c = self._from_qt(qc)
        self._cookies.pop((c["domain"], c["path"], c["name"]), None)

    def _finish(self):
        if not self.isVisible():
            return
        accounts.save(self.platform, list(self._cookies.values()))
        self.accept()


def sign_in(parent: QWidget, platform: str, settings: Settings) -> bool:
    """Make a session available for `platform`. True when there is something new to retry with."""
    if platform not in accounts.PLATFORMS:
        return False
    if accounts.default_browser() == "firefox":
        # Firefox keeps its session readable while it runs, so its open login is used directly
        settings.cookies_browser = "firefox"
        settings.save()
        return True
    return LoginDialog(platform, parent).exec() == QDialog.DialogCode.Accepted
