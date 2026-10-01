"""
Servicio de QR: la única puerta entre Streamlit y el motor heredado.

No reimplementa nada. Reutiliza tal cual:
  - intelliqr/core/qr_engine/generator.py  (QRGenerator, QRDesignOptions)
  - intelliqr/core/qr_engine/designer.py   (apply_frame, FrameOptions)
  - intelliqr/core/qr_engine/exporter.py   (QRExporter, ExportOptions)
  - intelliqr/core/qr_engine/validator.py  (límites de payload y logo)
  - intelliqr/qr_types/                    (los 12 tipos y sus validaciones)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from typing import Any

from utils.helpers import bootstrap_legacy_path

bootstrap_legacy_path()

from PIL import Image  # noqa: E402

from core.qr_engine.generator import QRGenerator, QRDesignOptions, QRGenerationResult  # noqa: E402
from core.qr_engine.designer import FrameOptions, apply_frame  # noqa: E402
from core.qr_engine.exporter import QRExporter, ExportOptions, resolve_size_cm  # noqa: E402
from core.qr_engine import validator as qr_validator  # noqa: E402
from qr_types.registry import get_all_types, get_type, get_categories  # noqa: E402
from qr_types.base import ValidationResult  # noqa: E402

logger = logging.getLogger("intelliqr.qr_service")

_generator = QRGenerator()
_exporter = QRExporter()

# Etiquetas de la UI → claves internas que el motor ya entiende.
PATTERNS = ["cuadrado", "redondeado", "puntos", "suave", "moderno"]
FRAME_STYLES = ["ninguno", "simple", "moderno", "redondeado", "etiqueta",
                "promocional", "circular", "telefono", "navegador", "bolsa"]
EXPORT_FORMATS = ["PNG", "JPG", "SVG", "PDF"]
SIZE_CHOICES = ["Original", "Pequeño", "Mediano", "Grande", "Personalizado"]


@dataclass
class DesignSettings:
    """Todo el diseño en un solo objeto serializable, para poder guardarlo en
    Google Sheets y reconstruir el mismo QR más adelante."""

    pattern: str = "cuadrado"
    fg_color: str = "#0F172A"
    bg_color: str = "#FFFFFF"
    gradient_enabled: bool = False
    gradient_start: str = "#2563EB"
    gradient_end: str = "#60A5FA"
    gradient_direction: str = "horizontal"
    box_size: int = 10
    border: int = 4
    logo_size_ratio: float = 0.22
    transparent_background: bool = False
    frame_style: str = "ninguno"
    frame_text: str = "ESCANÉAME"
    frame_color: str = "#2563EB"
    frame_text_color: str = "#FFFFFF"
    frame_scale: float = 1.0
    frame_font_size: int = 28

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str | None) -> "DesignSettings":
        if not raw:
            return cls()
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            logger.info("design_json inválido, se usa el diseño por defecto.")
            return cls()
        valid = {f: data[f] for f in cls.__dataclass_fields__ if f in data}
        return cls(**valid)


def build_qr_image(payload: str, design: DesignSettings,
                   logo_bytes: Any | None = None) -> tuple[Image.Image, list[str]]:
    """payload + diseño → imagen PIL lista para mostrar/exportar.

    Devuelve también los avisos del motor (logo demasiado grande, etc.).
    """
    warnings: list[str] = []

    size_warning = qr_validator.check_payload_size(payload)
    if size_warning:
        raise ValueError(size_warning)

    options = QRDesignOptions(
        pattern=design.pattern,
        fg_color=design.fg_color,
        bg_color=design.bg_color,
        gradient_enabled=design.gradient_enabled,
        gradient_start=design.gradient_start,
        gradient_end=design.gradient_end,
        gradient_direction=design.gradient_direction,
        logo_bytes=logo_bytes,
        logo_size_ratio=design.logo_size_ratio,
        box_size=design.box_size,
        border=design.border,
        transparent_background=design.transparent_background,
    )

    result: QRGenerationResult = _generator.generate(payload, options)
    warnings.extend(result.warnings)

    image = result.image
    if design.frame_style != "ninguno":
        # El marco se pinta sobre RGB; si el fondo era transparente lo
        # aplanamos primero para que el marco no salga con bordes sucios.
        frame_options = FrameOptions(
            style=design.frame_style,
            text=design.frame_text,
            text_color=design.frame_text_color,
            frame_color=design.frame_color,
            font_size=design.frame_font_size,
            frame_scale=design.frame_scale,
        )
        image = apply_frame(image.convert("RGB"), frame_options)

    return image, warnings


def export_qr(image: Image.Image, fmt: str, payload: str, name: str,
              size_choice: str = "Original", dpi: int = 300,
              custom_w: float | None = None, custom_h: float | None = None) -> bytes:
    """Genera los bytes descargables reutilizando QRExporter."""
    size_cm = None if size_choice == "Original" else resolve_size_cm(size_choice, custom_w, custom_h)
    options = ExportOptions(fmt=fmt, dpi=dpi, size_cm=size_cm, name=name)
    return _exporter.export_bytes(image, options, payload=payload)


# ------------------------------------------------------------ tipos estáticos
def list_static_types() -> list[Any]:
    return get_all_types()


def list_static_categories() -> dict[str, list[Any]]:
    return get_categories()


def validate_static_content(type_id: str, data: dict[str, Any]) -> ValidationResult:
    return get_type(type_id).validate(data)


def build_static_payload(type_id: str, data: dict[str, Any]) -> str:
    return get_type(type_id).build_payload(data)


def get_form_schema(type_id: str) -> list[Any]:
    """Los esquemas de formulario ya existían para la UI de escritorio y son
    independientes de Qt, así que Streamlit los reutiliza sin cambios."""
    from ui.qr.form_schemas import FORM_SCHEMAS

    return FORM_SCHEMAS.get(type_id, [])
