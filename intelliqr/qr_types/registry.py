"""Registro central de tipos de QR. Añadir un tipo nuevo = una línea aquí."""
from __future__ import annotations
from .base import QRType
from .url import URLType
from .whatsapp import WhatsAppType
from .email import EmailType
from .phone import PhoneType
from .sms import SMSType
from .wifi import WiFiType
from .vcard import VCardType
from .text import TextType
from .location import LocationType, GoogleMapsType
from .event import EventType
from .sepa import SEPATransferType

_ALL_TYPES: list[QRType] = [
    URLType(),
    GoogleMapsType(),
    WhatsAppType(),
    PhoneType(),
    SMSType(),
    EmailType(),
    VCardType(),
    TextType(),
    WiFiType(),
    EventType(),
    LocationType(),
    SEPATransferType(),
]

_BY_ID: dict[str, QRType] = {t.type_id: t for t in _ALL_TYPES}


def get_all_types() -> list[QRType]:
    return list(_ALL_TYPES)


def get_type(type_id: str) -> QRType:
    if type_id not in _BY_ID:
        raise KeyError(f"Tipo de QR desconocido: {type_id}")
    return _BY_ID[type_id]


def get_categories() -> dict[str, list[QRType]]:
    categories: dict[str, list[QRType]] = {}
    for t in _ALL_TYPES:
        categories.setdefault(t.category, []).append(t)
    return categories
