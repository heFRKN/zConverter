from pathlib import Path

# Flat, quiet palette. The accent is used sparingly: primary action, active states, selection.
ACCENT = "#990033"
ACCENT_HOVER = "#AB0A3E"
ACCENT_PRESS = "#80002B"
BG = "#111012"
SIDEBAR = "#151416"
SURFACE = "#19181A"
SURFACE_2 = "#211F22"
SURFACE_3 = "#2B292C"
BORDER = "#2A282B"
TEXT = "#ECE9EA"
TEXT_2 = "#9C979A"
TEXT_3 = "#6A6568"
ERROR = "#E5677D"
FONT_TEXT = "Segoe UI Variable Text"
FONT_DISPLAY = "Segoe UI Variable Display"


def stylesheet(chevron: Path) -> str:
    chevron_url = chevron.as_posix()
    return f"""
* {{ outline: none; }}
QWidget {{
    color: {TEXT};
    font-family: "{FONT_TEXT}", "Segoe UI";
    font-size: 13px;
}}
QMainWindow, QDialog {{ background: {BG}; }}
QLabel {{ background: transparent; }}
QLabel#H1 {{ font-family: "{FONT_DISPLAY}", "Segoe UI"; font-size: 24px; font-weight: 600; }}
QLabel#H2 {{ font-size: 14px; font-weight: 600; }}
QLabel#Sub {{ color: {TEXT_2}; }}
QLabel#Section {{ color: {TEXT_3}; font-size: 11px; font-weight: 600; letter-spacing: 1px; }}
QLabel#Caption {{ color: {TEXT_3}; font-size: 12px; }}
QLabel#Muted {{ color: {TEXT_2}; }}
QLabel#Muted:disabled {{ color: {TEXT_3}; }}
QLabel#Error {{ color: {ERROR}; font-size: 12px; }}
QLabel#Chip {{
    background: {SURFACE_2};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 1px 7px;
    color: {TEXT_2};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#Time {{ color: {TEXT}; font-size: 12px; font-weight: 600; }}

QFrame#Sidebar {{ background: {SIDEBAR}; border-right: 1px solid {BORDER}; }}

QLineEdit, QSpinBox {{
    background: {SURFACE_2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 0 10px;
    min-height: 34px;
    selection-background-color: {ACCENT};
}}
QLineEdit:hover, QSpinBox:hover {{ border-color: #3A373B; }}
QLineEdit:focus, QSpinBox:focus {{ border-color: {ACCENT}; }}
QLineEdit:disabled, QSpinBox:disabled {{ color: {TEXT_3}; background: {SURFACE}; }}
QLineEdit#Hero {{ min-height: 42px; font-size: 14px; padding-left: 14px; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}

QComboBox {{
    background: {SURFACE_2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 0 28px 0 10px;
    min-height: 34px;
}}
QComboBox:hover {{ border-color: #3A373B; }}
QComboBox:disabled {{ color: {TEXT_3}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{ image: url("{chevron_url}"); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE_2};
    border: 1px solid {BORDER};
    padding: 4px;
    selection-background-color: {SURFACE_3};
    selection-color: {TEXT};
    outline: none;
}}
QComboBox QAbstractItemView::item {{ min-height: 28px; padding: 0 8px; }}

QPushButton {{
    background: {SURFACE_2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 0 14px;
    min-height: 34px;
}}
QPushButton:hover {{ background: {SURFACE_3}; }}
QPushButton:pressed {{ background: {SURFACE}; }}
QPushButton:disabled {{ color: {TEXT_3}; background: {SURFACE}; }}
QPushButton#Primary {{
    background: {ACCENT};
    border: none;
    color: white;
    font-weight: 600;
    padding: 0 22px;
    min-height: 38px;
}}
QPushButton#Primary:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#Primary:pressed {{ background: {ACCENT_PRESS}; }}
QPushButton#Primary:disabled {{ background: #4A1A2B; color: rgba(255, 255, 255, 0.45); }}
QPushButton#Icon {{
    background: transparent;
    border: none;
    border-radius: 6px;
    min-height: 30px; max-height: 30px;
    min-width: 30px; max-width: 30px;
    padding: 0;
}}
QPushButton#Icon:hover {{ background: {SURFACE_3}; }}
QPushButton#Link {{ background: transparent; border: none; color: {TEXT_2}; padding: 0; min-height: 0; }}
QPushButton#Link:hover {{ color: {TEXT}; }}
QPushButton#Nav {{
    text-align: left;
    padding: 0 12px;
    min-height: 36px;
    border: none;
    border-left: 2px solid transparent;
    border-radius: 0;
    background: transparent;
    color: {TEXT_2};
}}
QPushButton#Nav:hover {{ color: {TEXT}; background: {SURFACE}; }}
QPushButton#Nav:checked {{ color: {TEXT}; background: {SURFACE_2}; border-left: 2px solid {ACCENT}; }}

QMenu {{ background: {SURFACE_2}; border: 1px solid {BORDER}; padding: 4px; }}
QMenu::item {{ padding: 6px 18px; }}
QMenu::item:selected {{ background: {SURFACE_3}; }}

QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {SURFACE_3}; border-radius: 3px; min-height: 30px; margin: 0 2px; }}
QScrollBar::handle:vertical:hover {{ background: #3A373B; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

QSlider::groove:horizontal {{ height: 4px; background: {SURFACE_3}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {TEXT}; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }}
QSlider::sub-page:horizontal:disabled {{ background: {SURFACE_3}; }}
QSlider::handle:horizontal:disabled, QSlider::handle:disabled {{ background: {TEXT_3}; }}

QTextBrowser {{ background: transparent; border: none; selection-background-color: {ACCENT}; }}
QToolTip {{ background: {SURFACE_2}; color: {TEXT}; border: 1px solid {BORDER}; padding: 5px 7px; }}
"""
