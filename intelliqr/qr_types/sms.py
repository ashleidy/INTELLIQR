from __future__ import annotations
import re
from typing import Any
from .base import QRType, ValidationResult


class SMSType(QRType):
    type_id = "sms"
    display_name = "SMS"
    category = "Comunicación"
    description = "Abre la app de mensajes con número y texto predefinidos."
    icon = "sms"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        number = (data.get("number") or "").strip()
        if not number or not re.fullmatch(r"\+?\d{5,15}", number):
            return ValidationResult.fail("number", "Introduce un número de teléfono válido.")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        number = data["number"].strip()
        message = (data.get("message") or "").strip()
        return f"SMSTO:{number}:{message}" if message else f"SMSTO:{number}:"
