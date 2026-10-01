
from __future__ import annotations
import glob
import os
import sys
from pathlib import Path

_EXE_NAMES_WIN = ("gswin64c.exe", "gswin32c.exe")
_EXE_NAMES_OTHER = ("gs",)


def _app_root() -> Path:
    """Carpeta base desde la que resolver rutas empaquetadas.

    En un .exe de PyInstaller (--onefile), los datos añadidos con
    --add-data se extraen a una carpeta temporal apuntada por sys._MEIPASS.
    En modo desarrollo, usamos la raíz del proyecto (carpeta 'intelliqr').
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent.parent


def _candidate_dirs() -> list[Path]:
    root = _app_root()
    candidates = [
        root / "ghostscript" / "bin",
        root / "vendor" / "ghostscript" / "bin",
    ]
    if sys.platform.startswith("win"):
        for base in (r"C:\Program Files\gs", r"C:\Program Files (x86)\gs"):
            candidates.extend(Path(p) / "bin" for p in glob.glob(base + r"\gs*"))
    return candidates


def _exe_names() -> tuple[str, ...]:
    return _EXE_NAMES_WIN if sys.platform.startswith("win") else _EXE_NAMES_OTHER


_ensured = False


def ensure_ghostscript_on_path() -> None:
    """Antepone al PATH la primera carpeta 'bin' de Ghostscript encontrada,
    para que treepoem (que internamente usa shutil.which) la vea. No hace
    nada si Ghostscript ya es localizable normalmente. Idempotente: solo
    hace el trabajo una vez por proceso."""
    global _ensured
    if _ensured:
        return
    _ensured = True

    import shutil
    if any(shutil.which(name) for name in _exe_names()):
        return  # ya está en el PATH (instalación normal del sistema)

    for directory in _candidate_dirs():
        if any((directory / name).exists() for name in _exe_names()):
            os.environ["PATH"] = f"{directory}{os.pathsep}{os.environ.get('PATH', '')}"
            return


def ghostscript_missing_hint() -> str:
    return (
        "Este tipo de código necesita Ghostscript instalado en el sistema (es gratuito). "
        "Descárgalo de https://www.ghostscript.com/releases/gsdnld.html y vuelve a intentarlo."
    )
