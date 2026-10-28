"""Free crop: a box over the image that can be moved, resized from any corner or edge, or redrawn
by dragging on the image. An optional aspect ratio keeps its shape."""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from . import theme

MIN = 8  # smallest box side in image pixels
_CURSORS = {
    "tl": Qt.CursorShape.SizeFDiagCursor, "br": Qt.CursorShape.SizeFDiagCursor,
    "tr": Qt.CursorShape.SizeBDiagCursor, "bl": Qt.CursorShape.SizeBDiagCursor,
    "t": Qt.CursorShape.SizeVerCursor, "b": Qt.CursorShape.SizeVerCursor,
    "l": Qt.CursorShape.SizeHorCursor, "r": Qt.CursorShape.SizeHorCursor,
    "move": Qt.CursorShape.SizeAllCursor,
}


class CropView(QWidget):
    changed = Signal()   # while dragging
    released = Signal()  # drag finished

    def __init__(self, height: int = 340):
        super().__init__()
        self.setMinimumHeight(height)
        self.setMouseTracking(True)
        self.pixmap: QPixmap | None = None
        self.iw = self.ih = 1
        self.box = QRectF()           # image pixels
        self.aspect: float | None = None
        self.circle = False
        self._drag = None
        self._anchor = QPointF()
        self._grab = QPointF()

    # ------------------------------------------------------------ state

    def set_image(self, px: QPixmap):
        self.pixmap = px
        self.iw, self.ih = max(1, px.width()), max(1, px.height())
        self.box = QRectF(0, 0, self.iw, self.ih)
        self.update()

    def set_box(self, box: tuple[int, int, int, int] | None):
        self.box = QRectF(0, 0, self.iw, self.ih) if not box else QRectF(box[0], box[1], box[2] - box[0],
                                                                          box[3] - box[1])
        self.update()

    def crop_box(self) -> tuple[int, int, int, int]:
        b = self.box
        return (max(0, round(b.left())), max(0, round(b.top())),
                min(self.iw, round(b.right())), min(self.ih, round(b.bottom())))

    def set_aspect(self, aspect: float | None, circle: bool = False):
        """Lock to a ratio; the box becomes the largest one of that ratio around its current centre."""
        self.aspect, self.circle = aspect, circle
        if aspect:
            w = min(self.iw, self.ih * aspect)
            h = w / aspect
            c = self.box.center() if not self.box.isEmpty() else QPointF(self.iw / 2, self.ih / 2)
            x = min(max(0.0, c.x() - w / 2), self.iw - w)
            y = min(max(0.0, c.y() - h / 2), self.ih - h)
            self.box = QRectF(x, y, w, h)
        self.update()

    # ------------------------------------------------------------ geometry

    def _view(self) -> tuple[QRectF, float]:
        r = QRectF(self.rect()).adjusted(14, 14, -14, -14)
        scale = min(r.width() / self.iw, r.height() / self.ih)
        w, h = self.iw * scale, self.ih * scale
        return QRectF(r.center().x() - w / 2, r.center().y() - h / 2, w, h), scale

    def _to_view(self, rect: QRectF) -> QRectF:
        v, s = self._view()
        return QRectF(v.left() + rect.left() * s, v.top() + rect.top() * s, rect.width() * s, rect.height() * s)

    def _to_img(self, p: QPointF) -> QPointF:
        v, s = self._view()
        return QPointF(min(max(0.0, (p.x() - v.left()) / s), self.iw), min(max(0.0, (p.y() - v.top()) / s), self.ih))

    def _handles(self) -> dict[str, QPointF]:
        b = self._to_view(self.box)
        pts = {"tl": b.topLeft(), "tr": b.topRight(), "bl": b.bottomLeft(), "br": b.bottomRight()}
        if not self.aspect:
            pts.update(t=QPointF(b.center().x(), b.top()), b=QPointF(b.center().x(), b.bottom()),
                       l=QPointF(b.left(), b.center().y()), r=QPointF(b.right(), b.center().y()))
        return pts

    def _hit(self, pos: QPointF) -> str | None:
        for name, pt in self._handles().items():
            if abs(pos.x() - pt.x()) <= 9 and abs(pos.y() - pt.y()) <= 9:
                return name
        if self._to_view(self.box).contains(pos):
            return "move"
        return None

    # ------------------------------------------------------------ mouse

    def mousePressEvent(self, e):
        if not self.pixmap:
            return
        pos = e.position()
        hit = self._hit(pos)
        b = self.box
        whole = b.width() >= self.iw - 1 and b.height() >= self.ih - 1
        if hit == "move" and whole:
            hit = None  # nothing selected yet: dragging on the image draws a new box
        if hit == "move":
            self._grab = self._to_img(pos) - b.topLeft()
        elif hit in ("tl", "tr", "bl", "br"):
            opposite = {"tl": b.bottomRight(), "tr": b.bottomLeft(), "bl": b.topRight(), "br": b.topLeft()}
            self._anchor = opposite[hit]
            hit = "corner"
        elif hit is None and self._view()[0].contains(pos):
            self._anchor = self._to_img(pos)  # draw a new box from here
            hit = "corner"
        self._drag = hit

    def mouseMoveEvent(self, e):
        pos = e.position()
        if not self._drag:
            hit = self._hit(pos)
            self.setCursor(_CURSORS.get(hit, Qt.CursorShape.CrossCursor if self._view()[0].contains(pos)
                                        else Qt.CursorShape.ArrowCursor))
            return
        p = self._to_img(pos)
        b = QRectF(self.box)
        if self._drag == "move":
            x = min(max(0.0, p.x() - self._grab.x()), self.iw - b.width())
            y = min(max(0.0, p.y() - self._grab.y()), self.ih - b.height())
            b.moveTo(x, y)
        elif self._drag == "corner":
            b = self._from_anchor(p)
        else:  # single edge, free ratio only
            if self._drag == "l":
                b.setLeft(min(p.x(), b.right() - MIN))
            elif self._drag == "r":
                b.setRight(max(p.x(), b.left() + MIN))
            elif self._drag == "t":
                b.setTop(min(p.y(), b.bottom() - MIN))
            else:
                b.setBottom(max(p.y(), b.top() + MIN))
        self.box = b
        self.update()
        self.changed.emit()

    def _from_anchor(self, p: QPointF) -> QRectF:
        a = self._anchor
        dx = 1 if p.x() >= a.x() else -1
        dy = 1 if p.y() >= a.y() else -1
        room_w = self.iw - a.x() if dx > 0 else a.x()
        room_h = self.ih - a.y() if dy > 0 else a.y()
        w = max(MIN, abs(p.x() - a.x()))
        h = max(MIN, abs(p.y() - a.y()))
        if self.aspect:
            if w / h > self.aspect:
                w = h * self.aspect
            else:
                h = w / self.aspect
            if w > room_w:
                w, h = room_w, room_w / self.aspect
            if h > room_h:
                h, w = room_h, room_h * self.aspect
        else:
            w, h = min(w, room_w), min(h, room_h)
        x = a.x() if dx > 0 else a.x() - w
        y = a.y() if dy > 0 else a.y() - h
        return QRectF(x, y, w, h)

    def mouseReleaseEvent(self, _):
        if self._drag:
            self._drag = None
            self.released.emit()

    # ------------------------------------------------------------ paint

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        frame = QPainterPath()
        frame.addRoundedRect(QRectF(self.rect()), 10, 10)
        p.fillPath(frame, QColor(theme.SURFACE_2))
        if not self.pixmap:
            return
        view, _ = self._view()
        p.drawPixmap(view, self.pixmap, QRectF(self.pixmap.rect()))
        b = self._to_view(self.box)

        outside = QPainterPath()
        outside.setFillRule(Qt.FillRule.OddEvenFill)
        outside.addRect(view)
        outside.addRect(b)
        p.fillPath(outside, QColor(0, 0, 0, 160))

        p.setPen(QPen(QColor(255, 255, 255, 55), 1))
        for i in (1, 2):
            x = b.left() + b.width() * i / 3
            y = b.top() + b.height() * i / 3
            p.drawLine(QPointF(x, b.top()), QPointF(x, b.bottom()))
            p.drawLine(QPointF(b.left(), y), QPointF(b.right(), y))
        if self.circle:
            pen = QPen(QColor(255, 255, 255, 170), 1.2, Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.drawEllipse(b)
        p.setPen(QPen(QColor(theme.ACCENT), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(b)
        p.setPen(QPen(QColor(theme.ACCENT), 1.5))
        p.setBrush(QColor("white"))
        for pt in self._handles().values():
            p.drawRect(QRectF(pt.x() - 4.5, pt.y() - 4.5, 9, 9))
