"""Visual trimming: frames at both cut points, a filmstrip / waveform timeline with
draggable handles, and short audio previews of each cut."""

import sys

from PySide6.QtCore import QRectF, QSize, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QGridLayout, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ..core import media, probe
from ..core.paths import app_dir
from ..i18n import t
from . import icons, theme
from .jobs import run_async
from .widgets import Thumb, hbox, label

FILMSTRIP = 10
LISTEN = 5.0  # seconds played around each cut
MIN_LEN = 0.5


def _px(data: bytes) -> QPixmap:
    px = QPixmap()
    px.loadFromData(data)
    return px


class RangeTimeline(QWidget):
    changed = Signal(str)    # which handle moved: start | end | both
    released = Signal(str)

    H = 11  # handle width

    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)
        self.setMouseTracking(True)
        self.duration = 1.0
        self.start = 0.0
        self.end = 1.0
        self.frames: list[QPixmap | None] = []
        self.wave: list[float] = []
        self._drag = None
        self._grab = 0.0

    def reset(self, duration: float):
        self.duration = max(duration, 0.1)
        self.start, self.end = 0.0, self.duration
        self.frames, self.wave = [], []
        self.update()

    def set_range(self, start: float, end: float):
        self.start = max(0.0, min(start, self.duration - MIN_LEN))
        self.end = min(self.duration, max(end, self.start + MIN_LEN))
        self.update()

    def _inner(self) -> QRectF:
        return QRectF(self.H, 0, self.width() - 2 * self.H, self.height())

    def _x(self, t: float) -> float:
        r = self._inner()
        return r.left() + t / self.duration * r.width()

    def _t(self, x: float) -> float:
        r = self._inner()
        return max(0.0, min(self.duration, (x - r.left()) / r.width() * self.duration))

    def _hit(self, x: float) -> str | None:
        xs, xe = self._x(self.start), self._x(self.end)
        if xs - self.H - 3 <= x <= xs + 4:
            return "start"
        if xe - 4 <= x <= xe + self.H + 3:
            return "end"
        if xs < x < xe:
            return "both"
        return None

    def mousePressEvent(self, e):
        x = e.position().x()
        hit = self._hit(x)
        if hit is None:  # click outside: move the closer handle there
            at = self._t(x)
            hit = "start" if abs(at - self.start) < abs(at - self.end) else "end"
            self._apply(hit, at)
        self._drag = hit
        self._grab = self._t(x) - self.start

    def mouseMoveEvent(self, e):
        x = e.position().x()
        if self._drag:
            self._apply(self._drag, self._t(x))
            return
        hit = self._hit(x)
        self.setCursor(Qt.CursorShape.SizeHorCursor if hit in ("start", "end") else
                       Qt.CursorShape.OpenHandCursor if hit == "both" else Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, _):
        if self._drag:
            self.released.emit(self._drag)
        self._drag = None

    def _apply(self, which: str, at: float):
        if which == "start":
            self.start = max(0.0, min(at, self.end - MIN_LEN))
        elif which == "end":
            self.end = min(self.duration, max(at, self.start + MIN_LEN))
        else:
            length = self.end - self.start
            s = max(0.0, min(at - self._grab, self.duration - length))
            self.start, self.end = s, s + length
        self.update()
        self.changed.emit(which)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = self._inner().adjusted(0, 4, 0, -4)
        clip = QPainterPath()
        clip.addRoundedRect(r, 4, 4)
        p.fillPath(clip, QColor(theme.SURFACE_2))

        p.save()
        p.setClipPath(clip)
        if self.frames:
            n = len(self.frames)
            slot = r.width() / n
            for i, px in enumerate(self.frames):
                if px is None or px.isNull():
                    continue
                cell = QRectF(r.left() + i * slot, r.top(), slot + 0.5, r.height())
                scale = max(cell.width() / px.width(), cell.height() / px.height())
                sw, sh = cell.width() / scale, cell.height() / scale
                src = QRectF((px.width() - sw) / 2, (px.height() - sh) / 2, sw, sh)
                p.drawPixmap(cell, px, src)
        elif self.wave:
            n = len(self.wave)
            bw = r.width() / n
            mid = r.center().y()
            p.setPen(Qt.PenStyle.NoPen)
            for i, v in enumerate(self.wave):
                x = r.left() + i * bw
                at = (i + 0.5) / n * self.duration
                inside = self.start <= at <= self.end
                p.setBrush(QColor(theme.TEXT_2 if inside else theme.TEXT_3))
                h = max(1.5, v * (r.height() - 8))
                p.drawRect(QRectF(x, mid - h / 2, max(1.0, bw - 1), h))
        xs, xe = self._x(self.start), self._x(self.end)
        shade = QColor(0, 0, 0, 165)
        p.fillRect(QRectF(r.left(), r.top(), xs - r.left(), r.height()), shade)
        p.fillRect(QRectF(xe, r.top(), r.right() - xe, r.height()), shade)
        p.restore()

        accent = QColor(theme.ACCENT)
        p.setPen(QPen(accent, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(int(xs), int(r.top()) + 1, int(xe), int(r.top()) + 1)
        p.drawLine(int(xs), int(r.bottom()) - 1, int(xe), int(r.bottom()) - 1)
        for x, left in ((xs, True), (xe, False)):
            hr = QRectF(x - self.H if left else x, r.top(), self.H, r.height())
            path = QPainterPath()
            path.addRoundedRect(hr, 3, 3)
            p.fillPath(path, accent)
            p.setPen(QPen(QColor(255, 255, 255, 200), 1.2))
            cx = hr.center().x()
            p.drawLine(int(cx), int(hr.center().y() - 6), int(cx), int(hr.center().y() + 6))


class _CutView(QWidget):
    """Frame at one cut point plus its time and a listen button."""

    def __init__(self, title: str):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.thumb = Thumb(320, 180)
        self.title = label(title.upper(), "Section")
        self.time = label("0:00.0", "Time")
        self.listen = QPushButton(" " + t("Dinle"))
        self.listen.setIcon(icons.icon("play", theme.TEXT_2))
        self.listen.setIconSize(QSize(13, 13))
        self.listen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.listen.setMinimumHeight(30)
        lay.addWidget(self.thumb)
        lay.addLayout(hbox(self.title, self.time, None, self.listen, spacing=8))


class TrimEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.info: probe.MediaInfo | None = None
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(3)
        self._gen = 0
        self._cache: dict[float, QPixmap] = {}
        self._playing = None
        self._play_n = 0

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self.cut_start = _CutView(t("Başlangıç"))
        self.cut_end = _CutView(t("Bitiş"))
        self.cuts = QWidget()
        grid = QGridLayout(self.cuts)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.addWidget(self.cut_start, 0, 0)
        grid.addWidget(self.cut_end, 0, 1)
        grid.setColumnStretch(2, 1)
        self.cuts.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        lay.addWidget(self.cuts)

        self.timeline = RangeTimeline()
        self.timeline.changed.connect(self._on_drag)
        self.timeline.released.connect(self._on_release)
        lay.addWidget(self.timeline)

        self.start_edit = QLineEdit()
        self.end_edit = QLineEdit()
        for w in (self.start_edit, self.end_edit):
            w.setFixedWidth(96)
            w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            w.setToolTip(t("Örnek: 1:30 ya da 1:30.5"))
            w.editingFinished.connect(self._on_typed)
        self.length = label("", "Muted")
        self.status = label("", "Caption")
        reset = QPushButton(t("Tamamını al"))
        reset.setObjectName("Link")
        reset.setCursor(Qt.CursorShape.PointingHandCursor)
        reset.clicked.connect(self.reset_range)
        lay.addLayout(hbox(self.start_edit, label("→", "Caption"), self.end_edit, 12, self.length, 12,
                           self.status, None, reset, spacing=8))

        self.cut_start.listen.clicked.connect(lambda: self._listen("start"))
        self.cut_end.listen.clicked.connect(lambda: self._listen("end"))
        self._debounce = {w: QTimer(self, singleShot=True, interval=160) for w in ("start", "end")}
        self._debounce["start"].timeout.connect(lambda: self._load_cut("start"))
        self._debounce["end"].timeout.connect(lambda: self._load_cut("end"))

    # ------------------------------------------------------------ public

    def load(self, info: probe.MediaInfo):
        self.stop()
        self._gen += 1
        self._cache.clear()
        self.info = info
        self.timeline.reset(info.duration)
        has_video = info.video is not None
        has_audio = info.audio is not None
        self.cuts.setVisible(has_video or has_audio)
        for cut in (self.cut_start, self.cut_end):
            cut.thumb.setVisible(has_video)
            cut.thumb.set_pixmap(None, t("Yükleniyor"))
            cut.listen.setVisible(has_audio)
        self._sync()
        if has_video:
            self._load_cut("start")
            self._load_cut("end")
            self._load_filmstrip()
        elif info.audio:
            self._load_wave()
        self.status.setText("" if (has_video or info.audio) else t("Önizleme yok"))

    def range(self) -> tuple[float | None, float | None]:
        """None for an untouched edge, so the full item is kept."""
        tl = self.timeline
        start = tl.start if tl.start > 0.05 else None
        end = tl.end if tl.end < tl.duration - 0.05 else None
        return start, end

    def reset_range(self):
        self.timeline.set_range(0, self.timeline.duration)
        self._sync()
        self._load_cut("start")
        self._load_cut("end")

    def stop(self):
        if self._playing and sys.platform == "win32":
            import winsound
            winsound.PlaySound(None, 0)
        self._set_playing(None)

    # ------------------------------------------------------------ timeline

    def _sync(self):
        tl = self.timeline
        self.start_edit.setText(media.format_precise(tl.start))
        self.end_edit.setText(media.format_precise(tl.end))
        self.cut_start.time.setText(media.format_precise(tl.start))
        self.cut_end.time.setText(media.format_precise(tl.end))
        whole = tl.start <= 0.05 and tl.end >= tl.duration - 0.05
        self.length.setText(t("Tamamı") + " · " + media.format_precise(tl.duration) if whole
                            else t("Seçim") + " · " + media.format_precise(tl.end - tl.start))

    def _on_drag(self, which: str):
        self._sync()
        for w in (("start", "end") if which == "both" else (which,)):
            self._debounce[w].start()

    def _on_release(self, which: str):
        for w in (("start", "end") if which == "both" else (which,)):
            self._debounce[w].stop()
            self._load_cut(w)

    def _on_typed(self):
        try:
            s = media.parse_time(self.start_edit.text()) or 0.0
            e = media.parse_time(self.end_edit.text())
        except ValueError:
            self._sync()
            return
        tl = self.timeline
        tl.set_range(s, tl.duration if e is None else e)
        self._sync()
        self._load_cut("start")
        self._load_cut("end")

    # ------------------------------------------------------------ previews

    def _load_cut(self, which: str):
        info = self.info
        if not info or not info.video:
            return
        tl = self.timeline
        # the last frame sits just before the end point
        at = tl.start if which == "start" else max(tl.start, tl.end - 0.1)
        key = round(at, 1)
        view = self.cut_start if which == "start" else self.cut_end
        if key in self._cache:
            view.thumb.set_pixmap(self._cache[key])
            return
        gen = self._gen

        def ok(data):
            if gen != self._gen:
                return
            px = _px(data)
            self._cache[key] = px
            now = tl.start if which == "start" else max(tl.start, tl.end - 0.1)
            if round(now, 1) == key:
                view.thumb.set_pixmap(px)

        def err(_):
            if gen == self._gen:
                view.thumb.set_pixmap(None, t("Kare alınamadı"))

        run_async(lambda: probe.frame(info.video, at), ok, err, self, pool=self.pool, priority=10)

    def _load_filmstrip(self):
        info, gen = self.info, self._gen
        d = info.duration
        self.timeline.frames = [None] * FILMSTRIP
        for i in range(FILMSTRIP):
            at = (i + 0.5) * d / FILMSTRIP

            def ok(data, i=i):
                if gen == self._gen:
                    self.timeline.frames[i] = _px(data)
                    self.timeline.update()

            run_async(lambda at=at: probe.frame(info.video, at, width=200), ok, lambda _: None, self,
                      pool=self.pool, priority=0)

    def _load_wave(self):
        info, gen = self.info, self._gen
        self.status.setText(t("Dalga formu hazırlanıyor"))

        def ok(wave):
            if gen == self._gen:
                self.timeline.wave = wave
                self.timeline.update()
                self.status.setText("")

        def err(_):
            if gen == self._gen:
                self.status.setText(t("Dalga formu alınamadı"))

        run_async(lambda: probe.waveform(info.audio), ok, err, self, pool=self.pool)

    # ------------------------------------------------------------ listening

    def _set_playing(self, which):
        self._playing = which
        for w, cut in (("start", self.cut_start), ("end", self.cut_end)):
            on = which == w
            cut.listen.setText(" " + (t("Durdur") if on else t("Dinle")))
            cut.listen.setIcon(icons.icon("stop" if on else "play", theme.TEXT if on else theme.TEXT_2))

    def _listen(self, which: str):
        if sys.platform != "win32" or not self.info or not self.info.audio:
            return
        import winsound

        if self._playing == which:
            self.stop()
            return
        self.stop()
        tl = self.timeline
        length = min(LISTEN, tl.end - tl.start)
        start = tl.start if which == "start" else tl.end - length
        self._play_n += 1
        path = str(app_dir() / "cache" / f"preview{self._play_n % 2}.wav")
        (app_dir() / "cache").mkdir(exist_ok=True)
        n = self._play_n
        view = self.cut_start if which == "start" else self.cut_end
        view.listen.setText(" " + t("Hazırlanıyor"))

        def ok(p):
            if n != self._play_n:
                return
            winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            self._set_playing(which)
            QTimer.singleShot(int(length * 1000) + 300, lambda: n == self._play_n and self._set_playing(None))

        def err(_):
            if n == self._play_n:
                self._set_playing(None)
                self.status.setText(t("Ses önizlemesi alınamadı"))

        run_async(lambda: probe.clip(self.info.audio, start, length, path), ok, err, self, pool=self.pool,
                  priority=20)
