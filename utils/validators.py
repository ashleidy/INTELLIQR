"""
Validaciones de la capa web (sección 18 del spec).

Devuelven mensajes amigables en español, nunca lanzan excepciones técnicas.
La validación de contenido por tipo de QR sigue viviendo donde ya vivía:
`intelliqr/qr_types/*.py` (cada QRType tiene su propio validate()).
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

# Sólo se permiten estos esquemas dentro de un QR: un QR que
# redirige a javascript:, data: o file: es un vector de ataque, no una
# funcionalidad.
ALLOWED_SCHEMES = ("http", "https")

_ID_PATTERN = re.compile(r"^[A-Z0-9]{4,12}$")


def validate_url(url: str) -> str | None:
    """Devuelve un mensaje de error, o None si la URL es válida."""
    url = (url or "").strip()
    if not url:
        return "Introduce la URL de destino."

    parsed = urlparse(url)
    if not parsed.scheme:
        return "La URL debe comenzar con http:// o https://."
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return "Sólo se permiten direcciones http:// o https://."
    if not parsed.netloc:
        return "La URL no parece completa. Ejemplo: https://tusitio.com/menu"
    if " " in url:
        return "La URL no puede contener espacios."
    if "." not in parsed.netloc and parsed.netloc != "localhost":
        return "El dominio no parece válido. Ejemplo: https://tusitio.com"
    return None


def validate_required(value: str, field_label: str) -> str | None:
    if not (value or "").strip():
        return f"El campo «{field_label}» es obligatorio."
    return None


def validate_qr_id(qr_id: str) -> str | None:
    if not _ID_PATTERN.match((qr_id or "").strip().upper()):
        return "El identificador no tiene un formato válido."
    return None


def validate_name(name: str) -> str | None:
    name = (name or "").strip()
    if not name:
        return "El nombre es obligatorio."
    if len(name) > 120:
        return "El nombre es demasiado largo (máximo 120 caracteres)."
    return None


def validate_create_form(nombre: str, url_destino: str) -> list[str]:
    """Valida el formulario de creación completo y devuelve todos los errores."""
    errors = [validate_name(nombre), validate_url(url_destino)]
    return [e for e in errors if e]
