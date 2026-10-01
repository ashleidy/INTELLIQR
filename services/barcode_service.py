"""
Servicio de códigos de barras.

Envoltorio delgado sobre `intelliqr/core/barcode_engine/`, que se conserva
intacto: el catálogo de ~39 simbologías BWIPP, la ayuda por tipo, los
ejemplos y el manejo de Ghostscript siguen siendo exactamente los mismos.

"""
from __future__ import annotations

import logging
from io import BytesIO
from typing import Any

from utils.helpers import bootstrap_legacy_path

bootstrap_legacy_path()

from PIL import Image  # noqa: E402

from core.barcode_engine import validator as barcode_validator  # noqa: E402

logger = logging.getLogger("intelliqr.barcode_service")

# treepoem se importa dentro del motor heredado. Si la librería no está
# instalada, la página de códigos de barras debe explicarlo, no reventar con
# un ImportError en pantalla.
try:
    from core.barcode_engine.generator import (  # noqa: E402
        BarcodeGenerator, TYPES, CATEGORIES, DISPLAY_NAMES, TWO_D_TYPES,
    )

    ENGINE_AVAILABLE = True
    _generator = BarcodeGenerator()
except Exception as _exc:  # noqa: BLE001
    logger.warning("Motor de códigos de barras no disponible: %s", _exc)
    ENGINE_AVAILABLE = False
    TYPES, CATEGORIES, DISPLAY_NAMES, TWO_D_TYPES = {}, {}, {}, set()
    _generator = None


class BarcodeUnavailable(Exception):
    """Ghostscript no está disponible en el entorno."""


# Solo las simbologías más usadas; el motor completo sigue disponible por debajo.
ESSENTIAL_TYPES = ["code128", "code39", "ean13", "ean8", "upca", "itf14"]


def list_types() -> list[str]:
    """Tipos esenciales que el motor realmente soporta."""
    return [t for t in ESSENTIAL_TYPES if t in TYPES]


def type_info(type_id: str) -> Any:
    return TYPES[type_id]


def display_name(type_id: str) -> str:
    return DISPLAY_NAMES.get(type_id, type_id)


def is_2d(type_id: str) -> bool:
    return type_id in TWO_D_TYPES


def validate(type_id: str, value: str) -> str | None:
    """Reutiliza `validate_barcode` tal cual. Más allá de comprobar que hay
    contenido, la autoridad real es BWIPP: valida cada simbología y calcula
    los dígitos de control, y su error ya llega traducido a lenguaje humano
    desde el generador."""
    result = barcode_validator.validate_barcode(type_id, value)
    return None if result.is_valid else result.message


def generate(type_id: str, value: str, show_text: bool = True, scale: int = 2) -> Image.Image:
    """Genera el código o lanza un error ya traducido a lenguaje humano."""
    if not ENGINE_AVAILABLE:
        raise BarcodeUnavailable(
            "El motor de códigos de barras no está instalado en este entorno."
        )
    try:
        return _generator.generate(type_id, value, show_text=show_text, scale=scale).image
    except ValueError as exc:
        message = str(exc)
        if "ghostscript" in message.lower():
            logger.warning("Ghostscript no disponible: %s", message)
            raise BarcodeUnavailable(message) from exc
        raise


def to_png_bytes(image: Image.Image, dpi: int = 300) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG", dpi=(dpi, dpi))
    return buf.getvalue()
