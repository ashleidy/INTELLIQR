
from __future__ import annotations
import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    return app_root().joinpath(*parts)


def find_app_icon() -> Path | None:
    """Busca el ícono de la app entre los nombres/formatos esperados.

    Se prueba primero el .ico (necesario para que Windows use un ícono
    nítido en varias resoluciones) y se cae a .jpeg/.png si es lo único
    disponible — QIcon puede cargar cualquiera de los dos para el ícono
    de ventana/barra de tareas en tiempo de ejecución, aunque solo el .ico
    sirve para --icon al compilar el .exe.
    """
    for name in ("LOGO.ico", "LOGO.png", "LOGO.jpeg", "LOGO.jpg"):
        candidate = resource_path(name)
        if candidate.exists():
            return candidate
    return None
