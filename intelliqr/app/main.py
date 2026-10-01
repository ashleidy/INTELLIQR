"""Punto de entrada de IntelliQR."""
from __future__ import annotations
import sys
from pathlib import Path

# Permitir imports absolutos tipo `from ui.xxx import ...` sin instalar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from app.config import APP_NAME, ORG_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_IDEAL_WIDTH, WINDOW_IDEAL_HEIGHT
from app.resources import find_app_icon
from app.window_sizing import compute_window_size, compute_centered_position
from database.database import init_db
from database.repositories.settings_repository import SettingsRepository
from ui.main_window import MainWindow
from ui import theme
from ui.i18n import set_language


def _fix_windows_taskbar_icon() -> None:
    
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"{ORG_NAME}.{APP_NAME}.1"
        )
    except Exception:
        pass  # en un equipo raro donde esto falle, seguimos sin romper la app


def main() -> int:
    _fix_windows_taskbar_icon()
    init_db()

    # Reparto correcto en pantallas de alta densidad (portátiles 4K, monitores
    # con escalado fraccional, etc.) — sección 41 del spec, "Responsive Desktop".
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)

    # Ícono de la app: antes se empaquetaba LOGO.jpeg con --add-data pero
    # nada lo asignaba como ícono, así que nunca se veía. find_app_icon()
    # ya resuelve la ruta correcta tanto en modo desarrollo como dentro del
    # .exe compilado (ver app/resources.py).
    icon_path = find_app_icon()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))

    # Aplicar idioma y tamaño de letra guardados de una sesión anterior
    # (Configuración > Idioma / Tamaño de letra) antes de construir la ventana.
    settings_repo = SettingsRepository()
    set_language(settings_repo.get("language", "es"))
    font_key = settings_repo.get("font_size", "normal")
    font_scale = theme.FONT_SCALE_OPTIONS.get(font_key, 1.0)
    app.setStyleSheet(theme.build_stylesheet(font_scale))

    window = MainWindow()
    if icon_path is not None:
        window.setWindowIcon(QIcon(str(icon_path)))

    # Tamaño inicial adaptado a la pantalla real del equipo (portátil pequeño,
    # monitor grande, lo que sea) en vez de un tamaño fijo que puede no caber
    # o dejar espacio vacío de más.
    screen = app.primaryScreen()
    if screen is not None:
        geometry = screen.availableGeometry()
        
        window.setMinimumSize(
            min(WINDOW_MIN_WIDTH, geometry.width()),
            min(WINDOW_MIN_HEIGHT, geometry.height()),
        )
        size = compute_window_size(
            geometry.width(), geometry.height(),
            WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
            WINDOW_IDEAL_WIDTH, WINDOW_IDEAL_HEIGHT,
        )
        window.resize(size.width, size.height)
        x, y = compute_centered_position(geometry.width(), geometry.height(), size.width, size.height)
        window.move(geometry.x() + x, geometry.y() + y)

    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
