"""Hand drawn 24px line icons, tinted at runtime."""

from functools import lru_cache

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_PATHS = {
    "download": '<path d="M12 4v11M7 10.5l5 5 5-5M5 19.5h14"/>',
    "user": '<circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20c1.4-3.7 4.2-5.6 7.5-5.6s6.1 1.9 7.5 5.6"/>',
    "sliders": '<path d="M4 7.5h9M18 7.5h2M4 16.5h3M11 16.5h9"/><circle cx="15.5" cy="7.5" r="2.2"/>'
               '<circle cx="8.5" cy="16.5" r="2.2"/>',
    "shield": '<path d="M12 3.5l7 2.8v5c0 4.4-2.9 7.9-7 9.6-4.1-1.7-7-5.2-7-9.6v-5z"/><path d="M9 12l2 2 4-4"/>',
    "folder": '<path d="M3.5 7.5a2 2 0 0 1 2-2h3.6l2 2h7.4a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/>',
    "paste": '<rect x="6" y="5" width="12" height="15.5" rx="2.2"/><path d="M9.5 5V4.2c0-.7.5-1.2 1.2-1.2h2.6c.7 0'
             ' 1.2.5 1.2 1.2V5M9 11h6M9 15h4"/>',
    "x": '<path d="M7 7l10 10M17 7L7 17"/>',
    "check": '<path d="M5.5 12.5l4 4L18.5 7.5"/>',
    "retry": '<path d="M4.5 12a7.5 7.5 0 1 0 2.3-5.4M4.5 4.5v4h4"/>',
    "lock": '<rect x="5.5" y="10.5" width="13" height="9.5" rx="2.2"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/>',
    "unlock": '<rect x="5.5" y="10.5" width="13" height="9.5" rx="2.2"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 6.8-1.2"/>',
    "chevron": '<path d="M7 10l5 5 5-5"/>',
    "search": '<circle cx="11" cy="11" r="6"/><path d="M19.5 19.5l-4-4"/>',
    "image": '<rect x="3.5" y="5" width="17" height="14" rx="2.2"/><circle cx="9" cy="10" r="1.6"/>'
             '<path d="M20.5 15.5l-5-4.5-8 8"/>',
}


def svg(name: str, color: str, stroke: float = 1.7) -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">'
            f'{_PATHS[name]}</svg>')


@lru_cache(maxsize=128)
def pixmap(name: str, color: str, size: int = 18, ratio: float = 2.0) -> QPixmap:
    px = QPixmap(int(size * ratio), int(size * ratio))
    px.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(svg(name, color).encode()))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p, QRectF(0, 0, px.width(), px.height()))
    p.end()
    px.setDevicePixelRatio(ratio)
    return px


def icon(name: str, color: str, size: int = 18, active: str | None = None) -> QIcon:
    ic = QIcon(pixmap(name, color, size))
    if active:
        ic.addPixmap(pixmap(name, active, size), QIcon.Mode.Normal, QIcon.State.On)
    return ic
