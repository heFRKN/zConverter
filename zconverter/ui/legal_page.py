from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QDialog, QPushButton, QTextBrowser, QVBoxLayout, QWidget

from ..core.paths import resource
from ..i18n import language, t
from . import theme
from .widgets import Backdrop, Card, Segmented, Toggle, hbox, label

DOCS = [("Kullanım koşulları", "TERMS.md"), ("Gizlilik ve KVKK", "PRIVACY.md"),
        ("Lisanslar", "THIRD_PARTY_NOTICES.md")]


TR_MARKER = "<!-- tr -->"


def read_doc(name: str) -> str:
    """Docs hold English first and Turkish after TR_MARKER; show the part for the current language."""
    try:
        text = resource(name).read_text(encoding="utf-8")
    except OSError:
        return t("{name} bulunamadı.", name=name)
    if TR_MARKER in text:
        en, tr = text.split(TR_MARKER, 1)
        return tr if language() == "tr" else en
    return text


def doc_view() -> QTextBrowser:
    view = QTextBrowser()
    view.setOpenExternalLinks(True)
    pal = view.palette()
    pal.setColor(QPalette.ColorRole.Text, QColor(theme.TEXT_2))
    pal.setColor(QPalette.ColorRole.Link, QColor("#E2507F"))
    view.setPalette(pal)
    view.document().setDocumentMargin(4)
    return view


class LegalPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 36, 40, 28)
        root.setSpacing(6)
        root.addWidget(label(t("Yasal"), "H1"))
        root.addWidget(label(t("Kısaca: kişisel kullanım için. İndirdiğin içerikten ve nasıl kullandığından sen "
                               "sorumlusun."), "Sub"))
        root.addSpacing(18)
        self.tabs = Segmented([t(name) for name, _ in DOCS])
        self.tabs.changed.connect(self._show)
        root.addWidget(self.tabs)
        root.addSpacing(10)
        card = Card(padding=22)
        self.view = doc_view()
        card.layout().addWidget(self.view)
        root.addWidget(card, 1)
        self._show(0)

    def _show(self, index: int):
        self.view.setMarkdown(read_doc(DOCS[index][1]))


class ConsentDialog(QDialog):
    """Shown once (and again when the terms change) before the app can be used."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("zConverter · " + t("Kullanım koşulları"))
        self.resize(720, 640)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        bg = Backdrop()
        outer.addWidget(bg)
        root = QVBoxLayout(bg)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(8)
        root.addWidget(label(t("Başlamadan önce"), "H1"))
        root.addWidget(label(t("zConverter yalnızca hakkın olan ya da kişisel kullanımına izin verilen içerikler "
                               "içindir. Lütfen koşulları oku."), "Sub", wrap=True))
        root.addSpacing(10)
        card = Card(padding=18)
        view = doc_view()
        view.setMarkdown(read_doc("TERMS.md"))
        card.layout().addWidget(view)
        root.addWidget(card, 1)
        root.addSpacing(8)
        self.agree = Toggle(t("Okudum, anladım ve kabul ediyorum"))
        quit_btn = QPushButton(t("Çık"))
        quit_btn.clicked.connect(self.reject)
        self.ok = QPushButton(t("Devam et"))
        self.ok.setObjectName("Primary")
        self.ok.setEnabled(False)
        self.ok.clicked.connect(self.accept)
        self.agree.toggled.connect(self.ok.setEnabled)
        for b in (quit_btn, self.ok, self.agree):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        root.addLayout(hbox(self.agree, None, quit_btn, self.ok))
