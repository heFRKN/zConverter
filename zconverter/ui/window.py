import ctypes
import sys

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QButtonGroup, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QMainWindow,
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
from .widgets import Backdrop, hbox, label


def paint_logo(p: QPainter, rect: QRectF):
    """The app mark: a flat crimson tile with a geometric 'z'. Also used for the .ico."""
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = rect.width()
    tile = QPainterPath()
    tile.addRoundedRect(rect, s * 0.24, s * 0.24)
    p.fillPath(tile, QColor(theme.ACCENT))
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
        bg = QColor(theme.BG)
        colorref = ctypes.c_int(bg.red() | bg.green() << 8 | bg.blue() << 16)
        dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(colorref), ctypes.sizeof(colorref))  # caption
        dwm.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(colorref), ctypes.sizeof(colorref))  # border
    except (AttributeError, OSError):
        pass


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("zConverter")
        self.resize(1200, 820)
        self.setMinimumSize(1040, 720)
        self.setAcceptDrops(True)
        self.manager = JobManager(settings.parallel)

        bg = Backdrop()
        self.setCentralWidget(bg)
        lay = QHBoxLayout(bg)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # sidebar
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(210)
        s = QVBoxLayout(side)
        s.setContentsMargins(0, 18, 0, 16)
        s.setSpacing(2)
        name = label("zConverter", "H2")
        name.setStyleSheet("font-size: 15px;")
        s.addLayout(hbox(Logo(26), name, None, spacing=10, margins=(18, 0, 0, 0)))
        s.addSpacing(24)

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
            b.setIconSize(QSize(17, 17))
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self.group.addButton(b, i)
            s.addWidget(b)
        self.group.button(0).setChecked(True)
        self.group.idClicked.connect(self._go)

        s.addStretch(1)
        foot = QVBoxLayout()
        foot.setContentsMargins(18, 0, 0, 0)
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
