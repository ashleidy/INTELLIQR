"""Clase base para todos los tipos de QR estáticos."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    is_valid: bool
    errors: dict[str, str] = field(default_factory=dict)  # campo -> mensaje amigable

    @staticmethod
    def ok() -> "ValidationResult":
        return ValidationResult(True, {})

    @staticmethod
    def fail(field_name: str, message: str) -> "ValidationResult":
        return ValidationResult(False, {field_name: message})


class QRType(ABC):
    """Contrato que debe cumplir cada tipo de QR estático."""

    #: identificador único, usado en la base de datos y en la UI
    type_id: str = "base"
    #: nombre mostrado al usuario
    display_name: str = "Base"
    #: categoría (Internet, Comunicación, Contacto, Conectividad, Eventos, Negocios, Archivos)
    category: str = "General"
    #: descripción corta para la tarjeta de selección
    description: str = ""
    #: nombre del icono lineal (clave lógica, no archivo)
    icon: str = "qr"

    @abstractmethod
    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Valida los campos del formulario. No lanza excepciones: devuelve errores amigables."""

    @abstractmethod
    def build_payload(self, data: dict[str, Any]) -> str:
        """Construye el string final que se codificará dentro del QR."""

    def default_data(self) -> dict[str, Any]:
        return {}
