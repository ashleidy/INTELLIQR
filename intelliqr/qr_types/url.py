from __future__ import annotations
from typing import Any
from .base import QRType, ValidationResult


class URLType(QRType):
    type_id = "url"
    display_name = "URL"
    category = "Internet"
    description = "Comparte un sitio web o cualquier enlace."
    icon = "link"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        url = (data.get("url") or "").strip()
        if not url:
            return ValidationResult.fail("url", "Introduce una URL.")
        if not (url.startswith("http://") or url.startswith("https://")):
            return ValidationResult.fail("url", "Introduce una URL válida (debe comenzar con http:// o https://).")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        return data["url"].strip()
