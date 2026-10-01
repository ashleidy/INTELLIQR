"""Identidad visual de IntelliQR: colores, tipografía y hoja de estilos (QSS).

Estilo: interfaz clara y moderna sobre fondo blanco, con bordes finos,
esquinas redondeadas, estados de foco visibles y neutros fríos.
"""

# ---- Color de marca -------------------------------------------------------
PRIMARY = "#2563EB"
PRIMARY_DARK = "#1E4FD8"
PRIMARY_DARKER = "#1A44BC"
PRIMARY_LIGHT = "#93B4FB"
PRIMARY_VERY_LIGHT = "#EEF4FF"
PRIMARY_SOFT = "#DFE9FE"

# ---- Neutros --------------------------------------------------------------
BACKGROUND = "#FFFFFF"       # fondo blanco en toda la app
SURFACE = "#FFFFFF"          # tarjetas y paneles
SURFACE_MUTED = "#F7F8FA"    # campos, zonas secundarias
SURFACE_HOVER = "#F2F4F7"
TEXT = "#0B1220"
TEXT_SECONDARY = "#6B7280"
TEXT_MUTED = "#9AA3AF"
BORDER = "#E8EAEF"
BORDER_STRONG = "#D7DBE3"

# ---- Semánticos -----------------------------------------------------------
SUCCESS = "#15A34A"
SUCCESS_LIGHT = "#ECFDF3"
WARNING = "#D97706"
WARNING_LIGHT = "#FFF7ED"
DANGER = "#DC2626"
DANGER_LIGHT = "#FEF2F2"

# Pila tipográfica moderna con respaldo en fuentes de sistema.
FONT_FAMILY = "Inter"
FONT_STACK = "'Inter', 'Segoe UI Variable Text', 'Segoe UI', 'Noto Sans', sans-serif"

# Radios y espaciados base
RADIUS_SM = 8
RADIUS_MD = 10
RADIUS_LG = 14

# Tamaños base (escala 1.0 = Normal). Configuración > Tamaño de letra
# multiplica todos estos valores por el factor elegido (0.9 / 1.0 / 1.15 / 1.3).
_BASE_BODY = 14
_BASE_H1 = 30
_BASE_H2 = 20
_BASE_H3 = 16
_BASE_CAPTION = 12


def build_stylesheet(font_scale: float = 1.0) -> str:
    """Genera la hoja de estilos QSS completa, escalando el tamaño de letra.
    Usada por Configuración > Tamaño de letra para agrandar/reducir el texto
    de toda la app sin tener que reiniciarla."""
    body = round(_BASE_BODY * font_scale)
    h1 = round(_BASE_H1 * font_scale)
    h2 = round(_BASE_H2 * font_scale)
    h3 = round(_BASE_H3 * font_scale)
    caption = round(_BASE_CAPTION * font_scale)

    return f"""
/* ---------- Base ---------- */
QWidget {{
    background-color: {BACKGROUND};
    color: {TEXT};
    font-family: {FONT_STACK};
    font-size: {body}px;
}}

QMainWindow, #ContentArea, QStackedWidget {{
    background-color: {BACKGROUND};
}}

QToolTip {{
    background-color: {TEXT};
    color: #FFFFFF;
    border: none;
    border-radius: {RADIUS_SM}px;
    padding: 6px 10px;
    font-size: {caption}px;
}}

/* ---------- Barra lateral ---------- */
#Sidebar {{
    background-color: {BACKGROUND};
    border-right: 1px solid {BORDER};
}}

#SidebarLogo {{
    font-size: {h3 + 3}px;
    font-weight: 700;
    letter-spacing: -0.3px;
    color: {TEXT};
    padding: 22px 20px 10px 20px;
}}

#SidebarSection {{
    font-size: {caption}px;
    font-weight: 700;
    letter-spacing: 1px;
    color: {TEXT_MUTED};
    padding: 14px 20px 6px 20px;
}}

#SidebarFooter {{
    font-size: {caption}px;
    color: {TEXT_MUTED};
    padding: 14px 20px 18px 20px;
    border-top: 1px solid {BORDER};
}}

QPushButton#NavButton {{
    text-align: left;
    padding: 10px 14px;
    margin: 1px 12px;
    border: none;
    border-radius: {RADIUS_MD}px;
    background-color: transparent;
    color: {TEXT_SECONDARY};
    font-size: {body}px;
    font-weight: 500;
}}

QPushButton#NavButton:hover {{
    background-color: {SURFACE_HOVER};
    color: {TEXT};
}}

QPushButton#NavButton[active="true"] {{
    background-color: {PRIMARY_VERY_LIGHT};
    color: {PRIMARY};
    font-weight: 600;
}}

/* ---------- Tarjetas y paneles ---------- */
QFrame#Card {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_LG}px;
}}

QFrame#Card:hover {{
    border: 1px solid {PRIMARY_LIGHT};
    background-color: {PRIMARY_VERY_LIGHT};
}}

QFrame#PreviewPanel {{
    background-color: {SURFACE_MUTED};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_LG}px;
}}

QFrame#StepIndicator {{
    background-color: transparent;
}}

QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: {RADIUS_LG}px;
    margin-top: 14px;
    padding: 14px 12px 10px 12px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: {TEXT_SECONDARY};
    font-size: {caption}px;
}}

QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {BORDER};
    background-color: {BORDER};
}}

/* ---------- Botones ---------- */
QPushButton#PrimaryButton {{
    background-color: {PRIMARY};
    color: #FFFFFF;
    border: none;
    border-radius: {RADIUS_MD}px;
    padding: 10px 20px;
    font-weight: 600;
}}
QPushButton#PrimaryButton:hover {{ background-color: {PRIMARY_DARK}; }}
QPushButton#PrimaryButton:pressed {{ background-color: {PRIMARY_DARKER}; }}
QPushButton#PrimaryButton:disabled {{
    background-color: {SURFACE_HOVER};
    color: {TEXT_MUTED};
}}

QPushButton#SecondaryButton {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER_STRONG};
    border-radius: {RADIUS_MD}px;
    padding: 10px 18px;
    font-weight: 600;
}}
QPushButton#SecondaryButton:hover {{
    background-color: {SURFACE_MUTED};
    border: 1px solid {PRIMARY_LIGHT};
    color: {PRIMARY};
}}
QPushButton#SecondaryButton:pressed {{ background-color: {SURFACE_HOVER}; }}
QPushButton#SecondaryButton:disabled {{ color: {TEXT_MUTED}; border-color: {BORDER}; }}

QPushButton#GhostButton {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    border: none;
    border-radius: {RADIUS_MD}px;
    padding: 9px 14px;
    font-weight: 600;
}}
QPushButton#GhostButton:hover {{ background-color: {SURFACE_HOVER}; color: {TEXT}; }}

QPushButton#DangerButton {{
    background-color: {DANGER_LIGHT};
    color: {DANGER};
    border: 1px solid #FBD5D5;
    border-radius: {RADIUS_MD}px;
    padding: 10px 18px;
    font-weight: 600;
}}
QPushButton#DangerButton:hover {{ background-color: #FDE4E4; }}

QPushButton {{
    background-color: {SURFACE};
    border: 1px solid {BORDER_STRONG};
    border-radius: {RADIUS_MD}px;
    padding: 8px 14px;
    color: {TEXT};
}}
QPushButton:hover {{ background-color: {SURFACE_MUTED}; }}
QPushButton:disabled {{ color: {TEXT_MUTED}; border-color: {BORDER}; }}

/* ---------- Campos ---------- */
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateTimeEdit, QDateEdit {{
    background-color: {SURFACE_MUTED};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD}px;
    padding: 9px 12px;
    selection-background-color: {PRIMARY_SOFT};
    selection-color: {TEXT};
}}
QLineEdit:hover, QComboBox:hover, QTextEdit:hover, QPlainTextEdit:hover,
QSpinBox:hover, QDoubleSpinBox:hover {{
    border: 1px solid {BORDER_STRONG};
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus, QDateEdit:focus {{
    background-color: {SURFACE};
    border: 1px solid {PRIMARY};
}}
QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled {{
    color: {TEXT_MUTED};
    background-color: {SURFACE_HOVER};
}}
QLineEdit[placeholderText] {{ color: {TEXT}; }}

QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD}px;
    padding: 4px;
    outline: none;
    selection-background-color: {PRIMARY_VERY_LIGHT};
    selection-color: {PRIMARY};
}}

QCheckBox, QRadioButton {{
    spacing: 8px;
    color: {TEXT};
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 17px;
    height: 17px;
    border: 1px solid {BORDER_STRONG};
    background-color: {SURFACE};
}}
QCheckBox::indicator {{ border-radius: 5px; }}
QRadioButton::indicator {{ border-radius: 9px; }}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{ border-color: {PRIMARY_LIGHT}; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {PRIMARY};
    border-color: {PRIMARY};
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {BORDER};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {PRIMARY};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {SURFACE};
    border: 2px solid {PRIMARY};
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 9px;
}}

QProgressBar {{
    background-color: {SURFACE_HOVER};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: {TEXT_SECONDARY};
}}
QProgressBar::chunk {{
    background-color: {PRIMARY};
    border-radius: 4px;
}}

/* ---------- Listas, tablas y pestañas ---------- */
QListView, QTreeView, QTableView {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_LG}px;
    outline: none;
    padding: 4px;
}}
QListView::item, QTreeView::item, QTableView::item {{
    padding: 8px;
    border-radius: {RADIUS_SM}px;
}}
QListView::item:hover, QTreeView::item:hover {{ background-color: {SURFACE_MUTED}; }}
QListView::item:selected, QTreeView::item:selected, QTableView::item:selected {{
    background-color: {PRIMARY_VERY_LIGHT};
    color: {PRIMARY};
}}
QHeaderView::section {{
    background-color: {SURFACE_MUTED};
    color: {TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px 10px;
    font-weight: 600;
    font-size: {caption}px;
}}

QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: {RADIUS_LG}px;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_SECONDARY};
    padding: 9px 16px;
    margin-right: 4px;
    border: none;
    border-radius: {RADIUS_MD}px;
    font-weight: 600;
}}
QTabBar::tab:hover {{ background: {SURFACE_HOVER}; color: {TEXT}; }}
QTabBar::tab:selected {{ background: {PRIMARY_VERY_LIGHT}; color: {PRIMARY}; }}

/* ---------- Scroll ---------- */
QScrollArea {{ border: none; background: transparent; }}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px 4px 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_STRONG};
    border-radius: 5px;
    min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{ background: {TEXT_MUTED}; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0 4px 2px 4px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_STRONG};
    border-radius: 5px;
    min-width: 32px;
}}
QScrollBar::handle:horizontal:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---------- Tipografía ---------- */
QLabel#H1 {{ font-size: {h1}px; font-weight: 700; letter-spacing: -0.6px; }}
QLabel#H2 {{ font-size: {h2}px; font-weight: 700; letter-spacing: -0.3px; }}
QLabel#H3 {{ font-size: {h3}px; font-weight: 600; }}
QLabel#Caption {{ font-size: {caption}px; color: {TEXT_SECONDARY}; }}
QLabel#ErrorLabel {{ font-size: {caption}px; color: {DANGER}; font-weight: 600; }}
QLabel#Subtitle {{ font-size: {body}px; color: {TEXT_SECONDARY}; }}

QLabel#Badge {{
    background-color: {SURFACE_MUTED};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
    border-radius: 999px;
    padding: 3px 10px;
    font-size: {caption}px;
    font-weight: 600;
}}
QLabel#BadgeAccent {{
    background-color: {PRIMARY_VERY_LIGHT};
    color: {PRIMARY};
    border: 1px solid {PRIMARY_SOFT};
    border-radius: 999px;
    padding: 3px 10px;
    font-size: {caption}px;
    font-weight: 600;
}}
QLabel#BadgeSuccess {{
    background-color: {SUCCESS_LIGHT};
    color: {SUCCESS};
    border: 1px solid #C8EFD6;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: {caption}px;
    font-weight: 600;
}}

/* ---------- Diálogos y menús ---------- */
QDialog {{ background-color: {BACKGROUND}; }}
QMenu {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD}px;
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 14px;
    border-radius: {RADIUS_SM}px;
}}
QMenu::item:selected {{
    background-color: {PRIMARY_VERY_LIGHT};
    color: {PRIMARY};
}}
"""


# Compatibilidad retroactiva: código existente que use theme.STYLESHEET
# directamente sigue funcionando con la escala normal (1.0).
STYLESHEET = build_stylesheet(1.0)

FONT_SCALE_OPTIONS = {
    "small": 0.9,
    "normal": 1.0,
    "large": 1.15,
    "xlarge": 1.3,
}
