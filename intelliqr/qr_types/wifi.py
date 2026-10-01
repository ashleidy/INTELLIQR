from __future__ import annotations
from typing import Any
from .base import QRType, ValidationResult


def _escape(value: str) -> str:
    """Escapa caracteres especiales según la especificación WIFI: de ZXing."""
    for ch in ["\\", ";", ",", ":", '"']:
        value = value.replace(ch, "\\" + ch)
    return value


class WiFiType(QRType):
    type_id = "wifi"
    display_name = "WiFi"
    category = "Conectividad"
    description = "Conecta a una red WiFi al escanear, sin escribir la contraseña."
    icon = "wifi"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        ssid = (data.get("ssid") or "").strip()
        security = data.get("security", "WPA/WPA2")
        password = (data.get("password") or "").strip()
        if not ssid:
            return ValidationResult.fail("ssid", "Introduce el nombre de la red (SSID).")
        if security != "Sin contraseña" and not password:
            return ValidationResult.fail("password", "Introduce la contraseña de la red.")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        ssid = _escape(data["ssid"].strip())
        security_map = {"WPA/WPA2": "WPA", "WEP": "WEP", "Sin contraseña": "nopass"}
        security = security_map.get(data.get("security", "WPA/WPA2"), "WPA")
        password = _escape((data.get("password") or "").strip())
        hidden = "true" if data.get("hidden") else "false"
        pass_part = f"P:{password};" if security != "nopass" else ""
        return f"WIFI:T:{security};S:{ssid};{pass_part}H:{hidden};;"
