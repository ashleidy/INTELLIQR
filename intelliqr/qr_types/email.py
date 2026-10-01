from __future__ import annotations
import re
from urllib.parse import quote
from typing import Any
from .base import QRType, ValidationResult

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailType(QRType):
    type_id = "email"
    display_name = "Email"
    category = "Comunicación"
    description = "Abre un correo nuevo con destinatario, asunto y mensaje."
    icon = "mail"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        email = (data.get("email") or "").strip()
        if not email or not EMAIL_RE.match(email):
            return ValidationResult.fail("email", "Introduce un correo electrónico válido.")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        email = data["email"].strip()
        subject = (data.get("subject") or "").strip()
        body = (data.get("message") or "").strip()
        params = []
        if subject:
            params.append(f"subject={quote(subject)}")
        if body:
            params.append(f"body={quote(body)}")
        query = "&".join(params)
        return f"mailto:{email}" + (f"?{query}" if query else "")
