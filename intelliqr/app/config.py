"""Configuración global de IntelliQR."""
from pathlib import Path

APP_NAME = "IntelliQR"
APP_VERSION = "1.0.0"
ORG_NAME = "IntelliQR"


DATA_DIR = Path.home() / "IntelliQR"


def _ensure_dir(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return path


_ensure_dir(DATA_DIR)

DATABASE_PATH = DATA_DIR / "intelliqr.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

PROJECTS_DIR = DATA_DIR / "projects"
_ensure_dir(PROJECTS_DIR)

EXPORTS_DIR = DATA_DIR / "exports"
_ensure_dir(EXPORTS_DIR)

LOGOS_DIR = DATA_DIR / "logos"
_ensure_dir(LOGOS_DIR)

WINDOW_MIN_WIDTH = 1024
WINDOW_MIN_HEIGHT = 640

WINDOW_IDEAL_WIDTH = 1280
WINDOW_IDEAL_HEIGHT = 768

# Niveles de corrección de errores de QR (mapeados por el generator)
DEFAULT_ERROR_CORRECTION = "M"
ERROR_CORRECTION_WITH_LOGO = "H"
