from __future__ import annotations
from typing import Any
from .base import QRType, ValidationResult


class LocationType(QRType):
    type_id = "location"
    display_name = "Ubicación"
    category = "Internet"
    description = "Abre un punto en el mapa mediante coordenadas."
    icon = "location"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        try:
            lat = float(data.get("latitude"))
            lon = float(data.get("longitude"))
        except (TypeError, ValueError):
            return ValidationResult.fail("latitude", "Introduce coordenadas numéricas válidas.")
        if not (-90 <= lat <= 90):
            return ValidationResult.fail("latitude", "La latitud debe estar entre -90 y 90.")
        if not (-180 <= lon <= 180):
            return ValidationResult.fail("longitude", "La longitud debe estar entre -180 y 180.")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        lat = float(data["latitude"])
        lon = float(data["longitude"])
        return f"geo:{lat},{lon}"


class GoogleMapsType(QRType):
    type_id = "google_maps"
    display_name = "Google Maps"
    category = "Internet"
    description = "Abre una dirección o coordenadas directamente en Google Maps."
    icon = "map"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        address = (data.get("address") or "").strip()
        lat = data.get("latitude")
        lon = data.get("longitude")
        url = (data.get("url") or "").strip()
        if not address and not url and not (lat and lon):
            return ValidationResult.fail("address", "Introduce una dirección, coordenadas o una URL de Maps.")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        url = (data.get("url") or "").strip()
        if url:
            return url
        lat, lon = data.get("latitude"), data.get("longitude")
        if lat and lon:
            return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        address = data["address"].strip().replace(" ", "+")
        return f"https://www.google.com/maps/search/?api=1&query={address}"
