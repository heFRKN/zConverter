"""Render the app mark to assets/icon.ico (multi-size) and assets/icon.png."""

import io
import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zconventer.ui.window import paint_logo  # noqa: E402


def render(size: int) -> Image.Image:
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    pad = size * 0.04
    paint_logo(p, QRectF(pad, pad, size - 2 * pad, size - 2 * pad))
    p.end()
    buf = QBuffer()
    buf.open(QBuffer.OpenModeFlag.ReadWrite)
    img.save(buf, "PNG")
    return Image.open(io.BytesIO(bytes(buf.data())))


def main():
    app = QGuiApplication(sys.argv)  # noqa: F841
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    big = render(512)
    big.save(out / "icon.png")
    sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    render(256).save(out / "icon.ico", sizes=[(s, s) for s in sizes])
    print("wrote", out / "icon.ico")


if __name__ == "__main__":
    main()
