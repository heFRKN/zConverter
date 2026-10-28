import random

from PySide6.QtCore import (QEasingCurve, QPointF, QRectF, QSize, Qt, QTimer, QVariantAnimation,
                            Signal)
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QImage, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap, QRadialGradient)
from PySide6.QtWidgets import (QAbstractButton, QFrame, QHBoxLayout, QLabel, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)

from . import icons, theme

_ACCENT = QColor(theme.ACCENT)


def _rgba(r, g, b, a):
    return QColor(r, g, b, a)


class Backdrop(QWidget):
    """Window background: deep near-black with soft crimson light and a fine grain."""

    _grain: QPixmap | None = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    @classmethod
    def grain(cls) -> QPixmap:
        if cls._grain is None:
            img = QImage(160, 160, QImage.Format.Format_ARGB32)
            rnd = random.Random(7)
            for y in range(160):
                for x in range(160):
                    v = rnd.randint(0, 255)
                    img.setPixelColor(x, y, QColor(v, v, v, 7))
            cls._grain = QPixmap.fromImage(img)
        return cls._grain

    def paintEvent(self, _):
        p = QPainter(self)
        r = self.rect()
        base = QLinearGradient(0, 0, 0, r.height())
        base.setColorAt(0, QColor("#0E0A0C"))
        base.setColorAt(1, QColor("#080607"))
        p.fillRect(r, base)

        def glow(cx, cy, radius, alpha):
            g = QRadialGradient(QPointF(cx, cy), radius)
            g.setColorAt(0, QColor(153, 0, 51, alpha))
            g.setColorAt(0.45, QColor(153, 0, 51, alpha // 3))
            g.setColorAt(1, QColor(153, 0, 51, 0))
            p.fillRect(r, g)

        w, h = r.width(), r.height()
        glow(w * 0.18, -h * 0.05, max(w, h) * 0.55, 70)
        glow(w * 1.02, h * 0.95, max(w, h) * 0.50, 42)
        glow(w * 0.75, h * 0.10, max(w, h) * 0.25, 14)
        p.drawTiledPixmap(r, self.grain())


class GlassCard(QFrame):
    """Translucent panel with a light top edge, like frosted glass catching light."""

    def __init__(self, parent=None, radius: float = 18, padding: int = 20, strength: float = 1.0):
        super().__init__(parent)
        self.radius = radius
        self.strength = strength
        self.highlight = False
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
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
        path = QPainterPath()
        path.addRoundedRect(rect, self.radius, self.radius)

        fill = QLinearGradient(0, 0, 0, rect.height())
        fill.setColorAt(0, _rgba(255, 255, 255, int(17 * self.strength)))
        fill.setColorAt(1, _rgba(255, 255, 255, int(8 * self.strength)))
        p.fillPath(path, fill)

        edge = QLinearGradient(0, 0, 0, rect.height())
        if self.highlight:
            edge.setColorAt(0, _rgba(230, 70, 120, 200))
            edge.setColorAt(1, _rgba(153, 0, 51, 140))
        else:
            edge.setColorAt(0, _rgba(255, 255, 255, 46))
            edge.setColorAt(0.35, _rgba(255, 255, 255, 16))
            edge.setColorAt(1, _rgba(255, 255, 255, 10))
        p.setPen(QPen(QBrush(edge), 1))
        p.drawPath(path)


class Segmented(QWidget):
    """Pill segmented control with a sliding glass thumb."""

    changed = Signal(int)

    def __init__(self, items: list[str], parent=None, height: int = 36):
        super().__init__(parent)
        self._items = list(items)
        self._disabled: set[int] = set()
        self._index = 0
        self._pos = 0.0
        self._h = height
        self._hover = -1
        self._anim = QVariantAnimation(self, duration=260, easingCurve=QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)  # focus ring only for keyboard users
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

    def text(self) -> str:
        return self._items[self._index]

    def set_index(self, index: int, animate: bool = True, emit: bool = True):
        if index == self._index or not 0 <= index < len(self._items):
            return
        self._index = index
        if animate and self.isVisible():
            self._anim.stop()
            self._anim.setStartValue(self._pos)
            self._anim.setEndValue(float(index))
            self._anim.start()
        else:
            self._pos = float(index)
            self.update()
        if emit:
            self.changed.emit(index)

    def _seg_w(self) -> float:
        fm = QFontMetrics(self._font())
        return max(fm.horizontalAdvance(t) for t in self._items) + 30

    def _font(self) -> QFont:
        f = QFont(self.font())
        f.setPixelSize(13)
        f.setWeight(QFont.Weight.Medium)
        return f

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
        rad = r.height() / 2
        track = QPainterPath()
        track.addRoundedRect(r, rad, rad)
        p.fillPath(track, _rgba(0, 0, 0, 80))
        p.setPen(QPen(_rgba(255, 255, 255, 20), 1))
        p.drawPath(track)

        sw = self._seg_w()
        thumb = QRectF(3 + self._pos * sw, 3, sw, r.height() - 5)
        tp = QPainterPath()
        tp.addRoundedRect(thumb, thumb.height() / 2, thumb.height() / 2)
        g = QLinearGradient(0, thumb.top(), 0, thumb.bottom())
        g.setColorAt(0, _rgba(255, 255, 255, 46))
        g.setColorAt(1, _rgba(255, 255, 255, 22))
        p.fillPath(tp, g)
        edge = QLinearGradient(0, thumb.top(), 0, thumb.bottom())
        edge.setColorAt(0, _rgba(255, 255, 255, 80))
        edge.setColorAt(1, _rgba(255, 255, 255, 12))
        p.setPen(QPen(QBrush(edge), 1))
        p.drawPath(tp)

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
        if self.hasFocus():
            p.setPen(QPen(_rgba(204, 40, 90, 150), 1.2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(track)


class Toggle(QAbstractButton):
    """Switch with an optional label on its right."""

    def __init__(self, text: str = "", parent=None, checked: bool = False):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setText(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._t = 1.0 if checked else 0.0
        self._anim = QVariantAnimation(self, duration=180, easingCurve=QEasingCurve.Type.OutCubic)
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
        w = 38
        if self.text():
            w += 10 + QFontMetrics(self.font()).horizontalAdvance(self.text())
        return QSize(w, 24)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = (self.height() - 22) / 2
        track = QRectF(0, y, 38, 22)
        off = _rgba(255, 255, 255, 34)
        on = QColor(_ACCENT)
        c = QColor(
            int(off.red() + (on.red() - off.red()) * self._t),
            int(off.green() + (on.green() - off.green()) * self._t),
            int(off.blue() + (on.blue() - off.blue()) * self._t),
            int(off.alpha() + (255 - off.alpha()) * self._t),
        )
        if not self.isEnabled():
            c.setAlpha(60)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawRoundedRect(track, 11, 11)
        knob_x = 2 + self._t * 16
        p.setBrush(_rgba(0, 0, 0, 50))
        p.drawEllipse(QRectF(knob_x, y + 2.6, 18, 18))
        p.setBrush(QColor("#F7F2F4") if self.isEnabled() else QColor(theme.TEXT_3))
        p.drawEllipse(QRectF(knob_x, y + 2, 18, 18))
        if self.text():
            p.setPen(QColor(theme.TEXT if self.isEnabled() else theme.TEXT_3))
            p.drawText(QRectF(48, 0, self.width() - 48, self.height()),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


class ProgressLine(QWidget):
    """Hairline progress. value=None shows a travelling highlight (unknown size)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
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
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_rgba(255, 255, 255, 20))
        p.drawRoundedRect(r, 2, 2)
        if self._error:
            p.setBrush(QColor(theme.ERROR))
            p.drawRoundedRect(r, 2, 2)
            return
        g = QLinearGradient(0, 0, r.width(), 0)
        g.setColorAt(0, QColor("#7C0029"))
        g.setColorAt(1, QColor("#D11A55"))
        p.setBrush(g)
        if self._value is None:
            x = (self._phase - 0.3) * r.width()
            p.drawRoundedRect(QRectF(x, 0, r.width() * 0.3, r.height()).intersected(r), 2, 2)
        elif self._value > 0:
            p.drawRoundedRect(QRectF(0, 0, r.width() * min(1.0, self._value), r.height()), 2, 2)


class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(40)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setPen(self.palette().color(self.foregroundRole()))
        p.setFont(self.font())
        text = self.fontMetrics().elidedText(self.text(), Qt.TextElideMode.ElideMiddle, self.width())
        p.drawText(self.rect(), int(self.alignment()) | Qt.AlignmentFlag.AlignVCenter, text)


class Badge(QWidget):
    """Monogram tile for a platform; no third-party logos are used."""

    def __init__(self, text: str, parent=None, size: int = 38):
        super().__init__(parent)
        self.text = text
        self.setFixedSize(size, size)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        g = QLinearGradient(0, 0, 0, r.height())
        g.setColorAt(0, QColor(170, 16, 66, 210))
        g.setColorAt(1, QColor(110, 0, 36, 210))
        path = QPainterPath()
        path.addRoundedRect(r, 10, 10)
        p.fillPath(path, g)
        p.setPen(QPen(_rgba(255, 255, 255, 50), 1))
        p.drawPath(path)
        f = QFont(self.font())
        f.setPixelSize(12)
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.text)


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
    b.setIconSize(QSize(18, 18))
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
