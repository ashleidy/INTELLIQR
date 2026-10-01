"""
Define, por cada tipo de QR, qué campos debe mostrar el formulario dinámico
(sección 10 del spec). Esto mantiene qr_content.py genérico: no necesita un
if/else por cada tipo, solo lee el esquema y construye los widgets.
"""
from __future__ import annotations
from dataclasses import dataclass, field

FieldKind = str  # "text" | "textarea" | "select" | "checkbox" | "number"


@dataclass
class FieldSchema:
    key: str
    label: str
    kind: FieldKind = "text"
    placeholder: str = ""
    options: list[str] = field(default_factory=list)
    default: object = ""
    required: bool = True


FORM_SCHEMAS: dict[str, list[FieldSchema]] = {
    "url": [
        FieldSchema("url", "URL", "text", "https://tusitio.com"),
    ],
    "google_maps": [
        FieldSchema("address", "Dirección", "text", "Calle 123, Ciudad", required=False),
        FieldSchema("url", "URL de Google Maps (opcional)", "text", "https://maps.google.com/...", required=False),
    ],
    "whatsapp": [
        FieldSchema("country_code", "Código de país", "text", "57"),
        FieldSchema("number", "Número", "text", "3001234567"),
        FieldSchema("message", "Mensaje predefinido", "textarea", "Hola, quiero más información...", required=False),
    ],
    "phone": [
        FieldSchema("country_code", "Código de país", "text", "57"),
        FieldSchema("number", "Número", "text", "3001234567"),
    ],
    "sms": [
        FieldSchema("number", "Número", "text", "+573001234567"),
        FieldSchema("message", "Mensaje", "textarea", "Escribe el mensaje...", required=False),
    ],
    "email": [
        FieldSchema("email", "Correo electrónico", "text", "correo@ejemplo.com"),
        FieldSchema("subject", "Asunto", "text", "", required=False),
        FieldSchema("message", "Mensaje", "textarea", "", required=False),
    ],
    "vcard": [
        FieldSchema("first_name", "Nombre", "text", "Juan"),
        FieldSchema("last_name", "Apellido", "text", "Pérez", required=False),
        FieldSchema("company", "Empresa", "text", "", required=False),
        FieldSchema("title", "Cargo", "text", "", required=False),
        FieldSchema("phone", "Teléfono", "text", "", required=False),
        FieldSchema("mobile", "Móvil", "text", "", required=False),
        FieldSchema("email", "Email", "text", "", required=False),
        FieldSchema("website", "Sitio web", "text", "", required=False),
        FieldSchema("address", "Dirección", "text", "", required=False),
        FieldSchema("city", "Ciudad", "text", "", required=False),
        FieldSchema("country", "País", "text", "", required=False),
    ],
    "text": [
        FieldSchema("text", "Texto", "textarea", "Escribe el contenido..."),
    ],
    "wifi": [
        FieldSchema("ssid", "Nombre de red (SSID)", "text", "MiRedWiFi"),
        FieldSchema("password", "Contraseña", "text", "", required=False),
        FieldSchema("security", "Tipo de seguridad", "select", options=["WPA/WPA2", "WEP", "Sin contraseña"], default="WPA/WPA2"),
        FieldSchema("hidden", "Red oculta", "checkbox", default=False, required=False),
    ],
    "event": [
        FieldSchema("name", "Nombre del evento", "text", "Lanzamiento de producto"),
        FieldSchema("date", "Fecha (AAAA-MM-DD)", "text", "2026-12-01"),
        FieldSchema("time", "Hora (HH:MM)", "text", "18:00", required=False),
        FieldSchema("location", "Ubicación", "text", "", required=False),
        FieldSchema("description", "Descripción", "textarea", "", required=False),
        FieldSchema("url", "URL relacionada", "text", "", required=False),
    ],
    "location": [
        FieldSchema("latitude", "Latitud", "text", "13.3540"),
        FieldSchema("longitude", "Longitud", "text", "-81.3670"),
    ],
    "sepa": [
        FieldSchema("beneficiary_name", "Nombre del beneficiario", "text", "Empresa S.A.S."),
        FieldSchema("iban", "IBAN", "text", "ES9121000418450200051332"),
        FieldSchema("bic", "BIC / SWIFT (opcional)", "text", "", required=False),
        FieldSchema("amount", "Monto en EUR (opcional)", "text", "25.50", required=False),
        FieldSchema("reference", "Referencia estructurada (opcional)", "text", "", required=False),
        FieldSchema("concept", "Concepto (opcional)", "textarea", "", required=False),
    ],
}
