from __future__ import annotations
import re
from urllib.parse import quote
from typing import Any
from .base import QRType, ValidationResult


class WhatsAppType(QRType):
    type_id = "whatsapp"
    display_name = "WhatsApp"
    category = "Comunicación"
    description = "Inicia una conversación de WhatsApp directamente."
    icon = "whatsapp"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        country_code = (data.get("country_code") or "").strip().lstrip("+")
        number = (data.get("number") or "").strip()
        if not country_code or not country_code.isdigit():
            return ValidationResult.fail("country_code", "Introduce un código de país válido.")
        if not number or not re.fullmatch(r"\d{5,15}", number):
            return ValidationResult.fail("number", "Introduce un número de teléfono válido.")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        country_code = data["country_code"].strip().lstrip("+")
        number = data["number"].strip()
        message = (data.get("message") or "").strip()
        full_number = f"{country_code}{number}"
        url = f"https://wa.me/{full_number}"
        if message:
            url += f"?text={quote(message)}"
        return url
