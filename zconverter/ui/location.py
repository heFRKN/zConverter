"""'Saving to: <folder>  Change  Open' row, shared by the pages. Changing it anywhere updates every row."""

import weakref
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QWidget

from ..core.settings import Settings
from ..i18n import t
from . import icons, theme
from .widgets import ElidedLabel, hbox, label

_rows: "weakref.WeakSet[SaveLocation]" = weakref.WeakSet()


def open_folder(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)
    QDesktopServices.openUrl(QUrl.fromLocalFile(path))


def change_folder(parent: QWidget, settings: Settings) -> bool:
    path = QFileDialog.getExistingDirectory(parent, t("Kayıt yeri"), settings.output_dir)
    if not path:
        return False
    settings.output_dir = str(Path(path))
    settings.save()
    for row in list(_rows):
        row.refresh()
    return True


class SaveLocation(QWidget):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        _rows.add(self)
        icon = QLabel()
        icon.setPixmap(icons.pixmap("folder", theme.TEXT_3, 15))
        icon.setFixedSize(QSize(16, 16))
        self.path = ElidedLabel("", middle=True)
        self.path.setObjectName("Muted")
        self.path.setCursor(Qt.CursorShape.PointingHandCursor)
        self.path.mousePressEvent = lambda _: open_folder(self.settings.output_dir)
        change = QPushButton(t("Değiştir"))
        change.setObjectName("Link")
        change.setCursor(Qt.CursorShape.PointingHandCursor)
        change.clicked.connect(lambda: change_folder(self, self.settings))
        open_btn = QPushButton(t("Aç"))
        open_btn.setObjectName("Link")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(lambda: open_folder(self.settings.output_dir))
        self.setLayout(hbox(icon, label(t("Kayıt yeri") + ":", "Caption"), self.path, 10, change, 12, open_btn,
                            spacing=6, stretch=(self.path,)))
        self.refresh()

    def refresh(self):
        self.path.setText(self.settings.output_dir)
        self.path.setToolTip(self.settings.output_dir)

    def showEvent(self, e):
        super().showEvent(e)
        self.refresh()
