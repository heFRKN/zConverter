from pathlib import Path

ACCENT = "#990033"
ACCENT_HOVER = "#B0103F"
ACCENT_PRESS = "#7C0029"
BG = "#0B0809"
TEXT = "#F2ECEE"
TEXT_2 = "#A89DA2"
TEXT_3 = "#6E6267"
ERROR = "#FF7A8F"
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
QLabel {{ background: transparent; }}
QLabel#H1 {{
    font-family: "{FONT_DISPLAY}", "Segoe UI";
    font-size: 27px;
    font-weight: 600;
}}
QLabel#H2 {{ font-size: 15px; font-weight: 600; }}
QLabel#Sub {{ color: {TEXT_2}; font-size: 13px; }}
QLabel#Section {{ color: {TEXT_3}; font-size: 11px; font-weight: 600; letter-spacing: 1px; }}
QLabel#Caption {{ color: {TEXT_3}; font-size: 12px; }}
QLabel#Muted {{ color: {TEXT_2}; }}
QLabel#Error {{ color: {ERROR}; font-size: 12px; }}
QLabel#Chip {{
    background: rgba(153, 0, 51, 0.20);
    border: 1px solid rgba(204, 40, 90, 0.45);
    border-radius: 8px;
    padding: 2px 8px;
    color: #F3C7D4;
    font-size: 11px;
    font-weight: 600;
}}

QLineEdit, QSpinBox {{
    background: rgba(0, 0, 0, 0.30);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 11px;
    padding: 0 12px;
    min-height: 36px;
    selection-background-color: {ACCENT};
}}
QLineEdit:hover, QSpinBox:hover {{ border-color: rgba(255, 255, 255, 0.15); }}
QLineEdit:focus, QSpinBox:focus {{ border-color: rgba(204, 40, 90, 0.85); background: rgba(0, 0, 0, 0.38); }}
QLineEdit:disabled, QSpinBox:disabled {{ color: {TEXT_3}; background: rgba(0, 0, 0, 0.15); }}
QLineEdit#Hero {{ min-height: 46px; font-size: 14px; padding-left: 16px; border-radius: 13px; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}

QComboBox {{
    background: rgba(0, 0, 0, 0.30);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 0 30px 0 12px;
    min-height: 36px;
}}
QComboBox:hover {{ border-color: rgba(255, 255, 255, 0.15); }}
QComboBox:disabled {{ color: {TEXT_3}; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{ image: url("{chevron_url}"); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{
    background: #181315;
    border: 1px solid rgba(255, 255, 255, 0.10);
    padding: 4px;
    selection-background-color: rgba(153, 0, 51, 0.65);
    selection-color: white;
    outline: none;
}}
QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 0 10px; border-radius: 6px; }}

QPushButton {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 10px;
    padding: 0 14px;
    min-height: 36px;
}}
QPushButton:hover {{ background: rgba(255, 255, 255, 0.10); border-color: rgba(255, 255, 255, 0.14); }}
QPushButton:pressed {{ background: rgba(255, 255, 255, 0.04); }}
QPushButton:disabled {{ color: {TEXT_3}; background: rgba(255, 255, 255, 0.03); }}
QPushButton#Primary {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #A90B40, stop:1 #8A002E);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 12px;
    color: white;
    font-weight: 600;
    padding: 0 24px;
    min-height: 40px;
}}
QPushButton#Primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #BB164C, stop:1 #990033);
}}
QPushButton#Primary:pressed {{ background: {ACCENT_PRESS}; }}
QPushButton#Primary:disabled {{ background: rgba(153, 0, 51, 0.30); color: rgba(255, 255, 255, 0.40); }}
QPushButton#Icon {{
    background: transparent;
    border: none;
    border-radius: 8px;
    min-height: 30px; max-height: 30px;
    min-width: 30px; max-width: 30px;
    padding: 0;
}}
QPushButton#Icon:hover {{ background: rgba(255, 255, 255, 0.08); }}
QPushButton#Link {{
    background: transparent;
    border: none;
    color: {TEXT_2};
    padding: 0;
    min-height: 0;
}}
QPushButton#Link:hover {{ color: {TEXT}; }}
QPushButton#Nav {{
    text-align: left;
    padding: 0 12px;
    min-height: 38px;
    border: 1px solid transparent;
    background: transparent;
    color: {TEXT_2};
    border-radius: 10px;
}}
QPushButton#Nav:hover {{ background: rgba(255, 255, 255, 0.045); color: {TEXT}; }}
QPushButton#Nav:checked {{
    background: rgba(255, 255, 255, 0.075);
    border: 1px solid rgba(255, 255, 255, 0.07);
    color: {TEXT};
}}

QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: rgba(255, 255, 255, 0.12); border-radius: 3px; min-height: 30px; margin: 0 2px; }}
QScrollBar::handle:vertical:hover {{ background: rgba(255, 255, 255, 0.22); }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

QSlider::groove:horizontal {{ height: 4px; background: rgba(255, 255, 255, 0.10); border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: #F4EEF0; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }}
QSlider::groove:horizontal:disabled {{ background: rgba(255, 255, 255, 0.05); }}
QSlider::sub-page:horizontal:disabled {{ background: rgba(255, 255, 255, 0.10); }}
QSlider::handle:horizontal:disabled, QSlider::handle:disabled {{ background: {TEXT_3}; }}
QLabel#Muted:disabled {{ color: {TEXT_3}; }}

QTextBrowser {{ background: transparent; border: none; selection-background-color: {ACCENT}; }}
QToolTip {{
    background: #1B1618;
    color: {TEXT};
    border: 1px solid rgba(255, 255, 255, 0.10);
    padding: 6px 8px;
}}
QDialog {{ background: {BG}; }}
"""
