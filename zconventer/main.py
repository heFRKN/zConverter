import os
import sys

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QDialog

from . import APP_NAME, AUTHOR, TERMS_VERSION, __version__
from .core.paths import app_dir, resource
from .core.settings import Settings
from .ui import icons, theme


def _prepare_streams():
    # A windowed build has no console; libraries that print must not crash.
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))


def _write_chevron():
    path = app_dir() / "chevron.svg"
    path.write_text(icons.svg("chevron", theme.TEXT_2, 2), encoding="utf-8")
    return path


def build_app(argv) -> QApplication:
    _prepare_streams()
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"{AUTHOR}.{APP_NAME}")
        except (AttributeError, OSError):
            pass
    app = QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(AUTHOR)
    font = QFont(theme.FONT_TEXT)
    font.setPixelSize(13)
    app.setFont(font)
    app.setStyleSheet(theme.stylesheet(_write_chevron()))
    icon_path = resource("assets/icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    return app


def main() -> int:
    app = build_app(sys.argv)
    from .ui.legal_page import ConsentDialog
    from .ui.window import MainWindow

    settings = Settings.load()
    if settings.accepted_terms < TERMS_VERSION:
        if ConsentDialog().exec() != QDialog.DialogCode.Accepted:
            return 0
        settings.accepted_terms = TERMS_VERSION
        settings.save()
    win = MainWindow(settings)
    win.show()
    return app.exec()
