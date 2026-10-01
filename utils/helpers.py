"""Utilidades compartidas por la capa web."""
from __future__ import annotations

import logging
import secrets
import sys
from datetime import datetime
from pathlib import Path

# Alfabeto sin caracteres ambiguos (0/O, 1/I/L): un identificador puede
# terminar leído por un humano desde una etiqueta impresa.
ID_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
ID_LENGTH = 6

_LOGGING_READY = False


def bootstrap_legacy_path() -> None:
    """Pone `intelliqr/` en sys.path.

    El motor original usa imports absolutos (`from core.qr_engine...`,
    `from qr_types...`) porque su raíz de proyecto era esa carpeta. En vez de
    reescribir decenas de imports —y arriesgarse a romper el generador, que
    es justo lo que el spec prohíbe— añadimos la carpeta al path y el código
    heredado sigue funcionando sin un solo cambio.
    """
    legacy_root = Path(__file__).resolve().parent.parent / "intelliqr"
    path = str(legacy_root)
    if path not in sys.path:
        sys.path.insert(0, path)


def setup_logging() -> None:
    """Los errores técnicos van al log; al usuario sólo le llegan mensajes
    amigables (sección 19 del spec)."""
    global _LOGGING_READY
    if _LOGGING_READY:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    _LOGGING_READY = True


def generate_qr_id(length: int = ID_LENGTH) -> str:
    """Identificador local (fallback y tests).

    En producción manda el servidor: Apps Script genera el ID dentro de la
    misma operación que escribe la fila, que es la única forma de garantizar
    unicidad sin condiciones de carrera.
    """
    return "".join(secrets.choice(ID_ALPHABET) for _ in range(length))


def format_date(value: str) -> str:
    """Fechas legibles sin reventar si el valor viene raro desde la hoja."""
    if not value:
        return "—"
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:19], fmt).strftime("%d/%m/%Y %H:%M")
        except ValueError:
            continue
    return value


def truncate(text: str, limit: int = 48) -> str:
    text = text or ""
    return text if len(text) <= limit else text[: limit - 1] + "…"


def safe_filename(name: str, default: str = "intelliqr") -> str:
    import re

    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name or "").strip().strip(".")
    return cleaned or default
