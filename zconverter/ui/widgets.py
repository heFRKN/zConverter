from PySide6.QtCore import QEasingCurve, QRectF, QSize, Qt, QTimer, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QAbstractButton, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)

from . import icons, theme


class Backdrop(QWidget):
    """Plain window background."""

    def paintEvent(self, _):
        QPainter(self).fillRect(self.rect(), QColor(theme.BG))


class Card(QFrame):
    """Flat surface with a hairline border."""

    def __init__(self, parent=None, radius: float = 12, padding: int = 20):
        super().__init__(parent)
        self.radius = radius
        self.highlight = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(padding, padding, padding, padding)
        lay.setSpacing(14)

    def set_highlight(self, on: bool):
        self.highlight = on
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(theme.ACCENT if self.highlight else theme.BORDER), 1))
        p.setBrush(QColor(theme.SURFACE))
        p.drawRoundedRect(rect, self.radius, self.radius)


class Segmented(QWidget):
    """Segmented control with a sliding thumb."""

    changed = Signal(int)

    def __init__(self, items: list[str], parent=None, height: int = 34):
        super().__init__(parent)
        self._items = list(items)
        self._disabled: set[int] = set()
        self._index = 0
        self._pos = 0.0
        self._h = height
        self._hover = -1
        self._anim = QVariantAnimation(self, duration=200, easingCurve=QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _on_anim(self, v):
        self._pos = v
        self.update()

    def set_items(self, items: list[str]):
        self._items = list(items)
        self._disabled.clear()
        self._index = min(self._index, len(items) - 1)
        self._pos = float(self._index)
        self.updateGeometry()
        self.update()

    def set_disabled(self, index: int, disabled: bool):
        (self._disabled.add if disabled else self._disabled.discard)(index)
        self.update()

    def index(self) -> int:
        return self._index

    def set_index(self, index: int, animate: bool = True, emit: bool = True):
        if index == self._index or not 0 <= index < len(self._items):
            return
        was_empty = self._index < 0
        self._index = index
        if animate and self.isVisible() and not was_empty:
            self._anim.stop()
            self._anim.setStartValue(self._pos)
            self._anim.setEndValue(float(index))
            self._anim.start()
        else:
            self._pos = float(index)
            self.update()
        if emit:
            self.changed.emit(index)

    def clear_selection(self):
        """No segment selected (e.g. the value came from somewhere else)."""
        self._anim.stop()
        self._index = -1
        self.update()

    def _font(self) -> QFont:
        f = QFont(self.font())
        f.setPixelSize(13)
        return f

    def _seg_w(self) -> float:
        fm = QFontMetrics(self._font())
        return max(fm.horizontalAdvance(t) for t in self._items) + 28

    def sizeHint(self):
        return QSize(int(self._seg_w() * len(self._items)) + 6, self._h)

    def _hit(self, x: float) -> int:
        i = int((x - 3) // self._seg_w())
        return i if 0 <= i < len(self._items) else -1

    def mouseMoveEvent(self, e):
        h = self._hit(e.position().x())
        if h != self._hover:
            self._hover = h
            self.update()

    def leaveEvent(self, _):
        self._hover = -1
        self.update()

    def mousePressEvent(self, e):
        i = self._hit(e.position().x())
        if i >= 0 and i not in self._disabled:
            self.set_index(i)

    def keyPressEvent(self, e):
        step = {Qt.Key.Key_Left: -1, Qt.Key.Key_Right: 1}.get(e.key())
        if step:
            i = self._index + step
            while 0 <= i < len(self._items) and i in self._disabled:
                i += step
            self.set_index(i)
        else:
            super().keyPressEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(theme.ACCENT if self.hasFocus() else theme.BORDER), 1))
        p.setBrush(QColor(theme.SURFACE_2))
        p.drawRoundedRect(r, 8, 8)
        sw = self._seg_w()
        if self._index >= 0:
            thumb = QRectF(3 + self._pos * sw, 3, sw, r.height() - 5)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(theme.SURFACE_3))
            p.drawRoundedRect(thumb, 6, 6)
        p.setFont(self._font())
        for i, t in enumerate(self._items):
            cell = QRectF(3 + i * sw, 0, sw, r.height())
            if i in self._disabled:
                p.setPen(QColor(theme.TEXT_3))
            elif i == self._index or i == self._hover:
                p.setPen(QColor(theme.TEXT))
            else:
                p.setPen(QColor(theme.TEXT_2))
            p.drawText(cell, Qt.AlignmentFlag.AlignCenter, t)


class Toggle(QAbstractButton):
    """Switch with an optional label on its right."""

    def __init__(self, text: str = "", parent=None, checked: bool = False):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setText(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._t = 1.0 if checked else 0.0
        self._anim = QVariantAnimation(self, duration=150, easingCurve=QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)
        self.toggled.connect(self._animate)

    def _on_anim(self, v):
        self._t = v
        self.update()

    def _animate(self, on):
        self._anim.stop()
        self._anim.setStartValue(self._t)
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    def sizeHint(self):
        w = 34
        if self.text():
            w += 10 + QFontMetrics(self.font()).horizontalAdvance(self.text())
        return QSize(w, 22)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = (self.height() - 18) / 2
        off, on = QColor(theme.SURFACE_3), QColor(theme.ACCENT)
        c = QColor(
            int(off.red() + (on.red() - off.red()) * self._t),
            int(off.green() + (on.green() - off.green()) * self._t),
            int(off.blue() + (on.blue() - off.blue()) * self._t),
        )
        if not self.isEnabled():
            c = QColor(theme.SURFACE_2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawRoundedRect(QRectF(0, y, 34, 18), 9, 9)
        p.setBrush(QColor("#F4F1F2") if self.isEnabled() else QColor(theme.TEXT_3))
        p.drawEllipse(QRectF(2 + self._t * 16, y + 2, 14, 14))
        if self.text():
            p.setPen(QColor(theme.TEXT if self.isEnabled() else theme.TEXT_3))
            p.drawText(QRectF(44, 0, self.width() - 44, self.height()),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


class ProgressLine(QWidget):
    """Thin progress bar. value=None shows a moving segment (unknown size)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self._value: float | None = 0.0
        self._phase = 0.0
        self._error = False
        self._timer = QTimer(self, interval=16)
        self._timer.timeout.connect(self._tick)

    def _tick(self):
        self._phase = (self._phase + 0.012) % 1.4
        self.update()

    def set_value(self, value: float | None, error: bool = False):
        self._value = value
        self._error = error
        if value is None and not self._timer.isActive():
            self._timer.start()
        elif value is not None:
            self._timer.stop()
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        r = QRectF(self.rect())
        p.fillRect(r, QColor(theme.SURFACE_3))
        if self._error:
            p.fillRect(r, QColor(theme.ERROR))
        elif self._value is None:
            x = (self._phase - 0.3) * r.width()
            p.fillRect(QRectF(x, 0, r.width() * 0.3, r.height()).intersected(r), QColor(theme.ACCENT))
        elif self._value > 0:
            p.fillRect(QRectF(0, 0, r.width() * min(1.0, self._value), r.height()), QColor(theme.ACCENT))


class ElidedLabel(QLabel):
    """Single line that shortens itself with '…'; middle=True keeps both ends (good for paths)."""

    def __init__(self, text="", parent=None, middle: bool = False):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(40)
        self._mode = Qt.TextElideMode.ElideMiddle if middle else Qt.TextElideMode.ElideRight

    def paintEvent(self, _):
        p = QPainter(self)
        p.setPen(self.palette().color(self.foregroundRole()))
        p.setFont(self.font())
        text = self.fontMetrics().elidedText(self.text(), self._mode, self.width())
        p.drawText(self.rect(), int(self.alignment()) | Qt.AlignmentFlag.AlignVCenter, text)


class Badge(QWidget):
    """Monogram tile for a platform; no third-party logos are used."""

    def __init__(self, text: str, parent=None, size: int = 34):
        super().__init__(parent)
        self.text = text
        self.setFixedSize(size, size)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(theme.BORDER), 1))
        p.setBrush(QColor(theme.SURFACE_2))
        p.drawRoundedRect(r, 8, 8)
        f = QFont(self.font())
        f.setPixelSize(11)
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.setPen(QColor(theme.TEXT_2))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.text)


class Thumb(QWidget):
    """Rounded image box; draws the image cropped to fill."""

    def __init__(self, w: int, h: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(w, h)
        self.pixmap = None
        self.message = ""

    def set_pixmap(self, px, message: str = ""):
        self.pixmap = px
        self.message = message
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(r, 8, 8)
        p.fillPath(path, QColor(theme.SURFACE_2))
        if self.pixmap and not self.pixmap.isNull():
            p.setClipPath(path)
            pw, ph = self.pixmap.width(), self.pixmap.height()
            scale = max(r.width() / pw, r.height() / ph)
            w, h = pw * scale, ph * scale
            p.drawPixmap(QRectF((r.width() - w) / 2, (r.height() - h) / 2, w, h), self.pixmap,
                         QRectF(self.pixmap.rect()))
        elif self.message:
            p.setPen(QColor(theme.TEXT_3))
            f = QFont(self.font())
            f.setPixelSize(12)
            p.setFont(f)
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.message)


def label(text: str, name: str | None = None, wrap: bool = False) -> QLabel:
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(wrap)
    return lb


def icon_button(name: str, tip: str, color: str = theme.TEXT_2) -> QPushButton:
    b = QPushButton()
    b.setObjectName("Icon")
    b.setIcon(icons.icon(name, color))
    b.setIconSize(QSize(17, 17))
    b.setToolTip(tip)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def field(title: str, widget: QWidget) -> QWidget:
    """Small caption above a control."""
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    lay.addWidget(label(title.upper(), "Section"))
    lay.addWidget(widget)
    return w


def hbox(*items, spacing: int = 10, margins=(0, 0, 0, 0), stretch=()) -> QHBoxLayout:
    """None = flexible gap, int = fixed gap. Items listed in `stretch` take the spare width."""
    lay = QHBoxLayout()
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    for it in items:
        if it is None:
            lay.addStretch(1)
        elif isinstance(it, int):
            lay.addSpacing(it)
        elif isinstance(it, QWidget):
            lay.addWidget(it, 1 if it in stretch else 0)
        else:
            lay.addLayout(it, 1 if it in stretch else 0)
    return lay
