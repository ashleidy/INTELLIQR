from __future__ import annotations
from typing import Any
from .base import QRType, ValidationResult

MAX_TEXT_LENGTH = 2000  # configurable


class TextType(QRType):
    type_id = "text"
    display_name = "Texto"
    category = "Contacto"
    description = "Codifica cualquier texto plano dentro del QR."
    icon = "text"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        text = data.get("text") or ""
        if not text.strip():
            return ValidationResult.fail("text", "Introduce un texto.")
        max_length = data.get("max_length", MAX_TEXT_LENGTH)
        if len(text) > max_length:
            return ValidationResult.fail("text", f"El texto supera el máximo de {max_length} caracteres.")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        return data["text"]
