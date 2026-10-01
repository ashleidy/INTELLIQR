from __future__ import annotations
import re
from typing import Any
from .base import QRType, ValidationResult


class PhoneType(QRType):
    type_id = "phone"
    display_name = "Teléfono"
    category = "Comunicación"
    description = "Al escanear, inicia una llamada directa."
    icon = "phone"

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
        return f"tel:+{country_code}{number}"
