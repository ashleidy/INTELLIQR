"""
Motor central de escaneo (sección 26 del spec).
Decodifica QR y códigos de barras a partir de una imagen (frame de cámara
o imagen cargada desde archivo), usando pyzbar (zbar) — la misma librería
soporta QR, EAN, UPC, Code128, Code39, Codabar, ITF, etc. en un solo paso.
"""
from __future__ import annotations
from dataclasses import dataclass

from PIL import Image
from pyzbar.pyzbar import decode as zbar_decode, ZBarSymbol

# Traduce los tipos internos de pyzbar a nombres amigables para el usuario.
_TYPE_LABELS = {
    "QRCODE": "Código QR",
    "EAN13": "EAN-13",
    "EAN8": "EAN-8",
    "UPCA": "UPC-A",
    "UPCE": "UPC-E",
    "CODE128": "Code 128",
    "CODE39": "Code 39",
    "CODABAR": "Codabar",
    "ITF": "ITF-14",
    "I25": "ITF-14",
}


@dataclass
class ScanResult:
    type_label: str          # nombre amigable, ej. "Código QR", "EAN-13"
    raw_type: str             # tipo crudo de pyzbar, ej. "QRCODE"
    content: str               # contenido decodificado
    rect: tuple[int, int, int, int]  # x, y, ancho, alto dentro de la imagen (para dibujar el recuadro)


class Scanner:
    def decode(self, image: Image.Image) -> list[ScanResult]:
        """Devuelve todos los códigos detectados en la imagen. Lista vacía si no hay ninguno."""
        try:
            decoded = zbar_decode(image.convert("RGB"))
        except Exception:
            return []

        results: list[ScanResult] = []
        for item in decoded:
            raw_type = item.type
            label = _TYPE_LABELS.get(raw_type, raw_type)
            try:
                content = item.data.decode("utf-8")
            except UnicodeDecodeError:
                content = item.data.decode("latin-1", errors="replace")
            rect = (item.rect.left, item.rect.top, item.rect.width, item.rect.height)
            results.append(ScanResult(type_label=label, raw_type=raw_type, content=content, rect=rect))
        return results


def classify_action(content: str) -> str | None:
    """Determina si el contenido escaneado se puede 'Abrir' directamente
    (URL, teléfono, email, etc.) y devuelve el esquema, o None si no aplica."""
    prefixes = ("http://", "https://", "mailto:", "tel:", "sms:", "geo:", "smsto:")
    lowered = content.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return content
    return None
