
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class BarcodeValidationResult:
    is_valid: bool
    message: str = ""
    corrected_value: str | None = None


def validate_barcode(barcode_type: str, value: str) -> BarcodeValidationResult:
    value = value.strip()
    if not value:
        return BarcodeValidationResult(False, "Introduce un contenido para generar el código.")
    return BarcodeValidationResult(True, "", value)
