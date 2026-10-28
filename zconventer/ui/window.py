import ctypes
import sys

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QButtonGroup, QGraphicsOpacityEffect, QHBoxLayout, QMainWindow,
                               QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from .. import AUTHOR, __version__
from ..core.platforms import detect
from ..core.settings import Settings
from . import icons, theme
from .download_page import DownloadPage
from .jobs import JobManager
from .legal_page import LegalPage
from .profile_page import ProfilePage
from .settings_page import SettingsPage
from .widgets import Backdrop, GlassCard, hbox, label


def paint_logo(p: QPainter, rect: QRectF):
    """The app mark: a crimson glass tile with a geometric 'z'. Also used for the .ico."""
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = rect.width()
    tile = QPainterPath()
    tile.addRoundedRect(rect, s * 0.26, s * 0.26)
    g = QLinearGradient(0, rect.top(), 0, rect.bottom())
    g.setColorAt(0, QColor("#B5134A"))
    g.setColorAt(1, QColor("#73002A"))
    p.fillPath(tile, g)
    sheen = QLinearGradient(0, rect.top(), 0, rect.top() + s * 0.55)
    sheen.setColorAt(0, QColor(255, 255, 255, 70))
    sheen.setColorAt(1, QColor(255, 255, 255, 0))
    p.fillPath(tile, sheen)
    p.setPen(QPen(QColor(255, 255, 255, 60), max(1.0, s / 40)))
    p.drawPath(tile)
    z = QPainterPath()
    x0, y0 = rect.left(), rect.top()
    z.moveTo(x0 + s * 0.31, y0 + s * 0.32)
    z.lineTo(x0 + s * 0.69, y0 + s * 0.32)
    z.lineTo(x0 + s * 0.31, y0 + s * 0.68)
    z.lineTo(x0 + s * 0.69, y0 + s * 0.68)
    pen = QPen(QColor("white"), s * 0.095)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.drawPath(z)


class Logo(QWidget):
    def __init__(self, size: int = 30):
        super().__init__()
        self.setFixedSize(size, size)

    def paintEvent(self, _):
        paint_logo(QPainter(self), QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5))


def _dark_title_bar(hwnd: int):
    """Match the native title bar to the app (Windows 11)."""
    if sys.platform != "win32":
        return
    try:
        dwm = ctypes.windll.dwmapi
        on = ctypes.c_int(1)
        dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(on), ctypes.sizeof(on))  # immersive dark mode
        bg = QColor("#0E0A0C")
        colorref = ctypes.c_int(bg.red() | bg.green() << 8 | bg.blue() << 16)
        dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(colorref), ctypes.sizeof(colorref))  # caption
        dwm.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(colorref), ctypes.sizeof(colorref))  # border
    except (AttributeError, OSError):
        pass


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("zConventer")
        self.resize(1200, 820)
        self.setMinimumSize(1040, 720)
        self.setAcceptDrops(True)
        self.manager = JobManager(settings.parallel)

        bg = Backdrop()
        self.setCentralWidget(bg)
        lay = QHBoxLayout(bg)
        lay.setContentsMargins(14, 14, 0, 14)
        lay.setSpacing(0)

        # sidebar
        side = GlassCard(radius=20, padding=14, strength=0.85)
        side.setFixedWidth(224)
        s = side.layout()
        s.setSpacing(4)
        name = label("zConventer", "H2")
        name.setStyleSheet("font-size: 16px;")
        s.addLayout(hbox(Logo(30), name, None, spacing=10, margins=(6, 6, 0, 0)))
        s.addSpacing(26)

        self.stack = QStackedWidget()
        self.download_page = DownloadPage(settings, self.manager)
        pages = [
            ("download", "İndir", self.download_page),
            ("user", "Profil görselleri", ProfilePage(settings)),
            ("sliders", "Ayarlar", SettingsPage(settings, self.manager)),
            ("shield", "Yasal", LegalPage()),
        ]
        self.group = QButtonGroup(self)
        for i, (ic, text, page) in enumerate(pages):
            self.stack.addWidget(page)
            b = QPushButton("  " + text)
            b.setObjectName("Nav")
            b.setCheckable(True)
            b.setIcon(icons.icon(ic, theme.TEXT_2, active=theme.TEXT))
            b.setIconSize(QSize(18, 18))
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self.group.addButton(b, i)
            s.addWidget(b)
        self.group.button(0).setChecked(True)
        self.group.idClicked.connect(self._go)

        s.addStretch(1)
        foot = QVBoxLayout()
        foot.setContentsMargins(8, 0, 0, 2)
        foot.setSpacing(2)
        foot.addWidget(label(f"Sürüm {__version__}", "Caption"))
        foot.addWidget(label(f"MIT · {AUTHOR}", "Caption"))
        s.addLayout(foot)

        lay.addWidget(side)
        lay.addWidget(self.stack, 1)
        self._fade = None

    def _go(self, index: int):
        if index == self.stack.currentIndex():
            return
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        self._fade = QPropertyAnimation(effect, b"opacity", self, duration=180,
                                        startValue=0.0, endValue=1.0,
                                        easingCurve=QEasingCurve.Type.OutCubic)
        self._fade.finished.connect(lambda: page.setGraphicsEffect(None))
        self._fade.start()

    def showEvent(self, e):
        super().showEvent(e)
        _dark_title_bar(int(self.winId()))

    # drop a link anywhere to start
    def dragEnterEvent(self, e):
        if e.mimeData().hasText() or e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        md = e.mimeData()
        text = md.urls()[0].toString() if md.hasUrls() else md.text()
        if detect(text):
            self.group.button(0).setChecked(True)
            self._go(0)
            self.download_page.set_url(text)
