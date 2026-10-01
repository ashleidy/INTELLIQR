
from __future__ import annotations


_APPROX_MAX_CHARS = 2900


def check_payload_size(payload: str) -> str | None:
    """Devuelve un mensaje amigable si el contenido es demasiado largo, o None si está bien."""
    if len(payload) > _APPROX_MAX_CHARS:
        return "El contenido es demasiado extenso para un código QR. Intenta acortarlo."
    return None


def check_logo_ratio(logo_size_ratio: float) -> str | None:
    if logo_size_ratio > 0.30:
        return "El logo es demasiado grande y puede afectar la lectura del código."
    return None
