from __future__ import annotations
from typing import Any
from .base import QRType, ValidationResult


class VCardType(QRType):
    type_id = "vcard"
    display_name = "VCard"
    category = "Contacto"
    description = "Comparte una tarjeta de contacto completa."
    icon = "contact"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        first_name = (data.get("first_name") or "").strip()
        if not first_name:
            return ValidationResult.fail("first_name", "Introduce al menos el nombre.")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        first = data.get("first_name", "").strip()
        last = data.get("last_name", "").strip()
        org = data.get("company", "").strip()
        title = data.get("title", "").strip()
        phone = data.get("phone", "").strip()
        mobile = data.get("mobile", "").strip()
        email = data.get("email", "").strip()
        website = data.get("website", "").strip()
        address = data.get("address", "").strip()
        city = data.get("city", "").strip()
        country = data.get("country", "").strip()

        lines = ["BEGIN:VCARD", "VERSION:3.0", f"N:{last};{first};;;", f"FN:{first} {last}".strip()]
        if org:
            lines.append(f"ORG:{org}")
        if title:
            lines.append(f"TITLE:{title}")
        if phone:
            lines.append(f"TEL;TYPE=WORK,VOICE:{phone}")
        if mobile:
            lines.append(f"TEL;TYPE=CELL:{mobile}")
        if email:
            lines.append(f"EMAIL:{email}")
        if website:
            lines.append(f"URL:{website}")
        if address or city or country:
            lines.append(f"ADR;TYPE=WORK:;;{address};{city};;;{country}")
        lines.append("END:VCARD")
        return "\n".join(lines)
