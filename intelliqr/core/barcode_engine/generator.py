
from __future__ import annotations
from dataclasses import dataclass

import treepoem
from PIL import Image

from core.barcode_engine.gs_locator import ensure_ghostscript_on_path, ghostscript_missing_hint


@dataclass
class TypeInfo:
    bwipp_type: str          # nombre del símbolo en BWIPP
    display_name: str         # nombre mostrado al usuario
    category: str              # categoría para agrupar en el selector
    placeholder: str            # texto de ejemplo dentro del campo
    example: str                  # "Ejemplo: ..." mostrado como ayuda
    help_text: str = ""           # explicación breve de qué introducir


# ---- Catálogo completo (sección 22, ampliado según tec-it.com) ----
TYPES: dict[str, TypeInfo] = {
    # Códigos lineales
    "code128": TypeInfo("code128", "Code 128", "Códigos lineales",
                         "PRODUCTO-00123", "PRODUCTO-00123",
                         "Acepta letras, números y símbolos. El más usado en logística e inventario."),
    "code39": TypeInfo("code39", "Code 39", "Códigos lineales",
                        "ABC-1234", "ABC-1234",
                        "Letras mayúsculas, números y algunos símbolos (- . espacio $ / + %)."),
    "code39ext": TypeInfo("code39ext", "Code 39 Extendido", "Códigos lineales",
                           "Producto #1", "Producto #1",
                           "Como Code 39, pero admite minúsculas y todos los caracteres ASCII."),
    "code93": TypeInfo("code93", "Code 93", "Códigos lineales",
                        "ABC-1234", "ABC-1234",
                        "Similar a Code 39 pero más compacto y con doble dígito de control."),
    "rationalizedCodabar": TypeInfo("rationalizedCodabar", "Codabar", "Códigos lineales",
                                     "A123456A", "A123456A",
                                     "Empieza y termina con una letra A-D. Usado en bibliotecas y bancos de sangre."),
    "interleaved2of5": TypeInfo("interleaved2of5", "ITF (Interleaved 2 of 5)", "Códigos lineales",
                                 "1234567890", "1234567890",
                                 "Solo números, en cantidad par. Común en cajas de embalaje."),
    "itf14": TypeInfo("itf14", "ITF-14", "Códigos lineales",
                       "1234567890123", "1234567890123 (13 dígitos, el de control se calcula solo)",
                       "Para unidades logísticas (cajas, pallets). 14 dígitos en el código final."),
    "msi": TypeInfo("msi", "MSI Plessey", "Códigos lineales",
                     "123456", "123456",
                     "Solo números. Usado en estanterías y control de inventario."),
    "gs1-128": TypeInfo("gs1-128", "GS1-128", "Códigos lineales",
                         "(01)04006381333931(17)221231", "(01)04006381333931(17)221231",
                         "Identificadores de aplicación GS1 entre paréntesis: (01) GTIN, (17) caducidad, (10) lote, etc."),

    # EAN / UPC
    "ean13": TypeInfo("ean13", "EAN-13", "EAN / UPC",
                       "400638133393", "400638133393 (12 dígitos, el de control se calcula solo)",
                       "El código de barras estándar de productos de retail en Europa/LatAm."),
    "ean8": TypeInfo("ean8", "EAN-8", "EAN / UPC",
                      "9638507", "9638507 (7 dígitos, el de control se calcula solo)",
                      "Versión reducida de EAN-13 para envases pequeños."),
    "upca": TypeInfo("upca", "UPC-A", "EAN / UPC",
                      "03600029145", "03600029145 (11 dígitos, el de control se calcula solo)",
                      "El estándar de retail en EE.UU. y Canadá."),
    "upce": TypeInfo("upce", "UPC-E", "EAN / UPC",
                      "01234565", "01234565",
                      "Versión comprimida de UPC-A para productos pequeños."),

    # GS1 DataBar
    "databaromni": TypeInfo("databaromni", "GS1 DataBar Omnidireccional", "GS1 DataBar",
                             "(01)09521234543213", "(01)09521234543213",
                             "Para productos pequeños de frutas/verduras a granel. Usa el identificador (01) + GTIN de 14 dígitos."),
    "databarexpanded": TypeInfo("databarexpanded", "GS1 DataBar Expandido", "GS1 DataBar",
                                 "(01)00012345678905(3103)000123", "(01)00012345678905(3103)000123",
                                 "Como GS1-128 pero más compacto; admite varios identificadores de aplicación."),
    "databarlimited": TypeInfo("databarlimited", "GS1 DataBar Limitado", "GS1 DataBar",
                                "(01)09521234543213", "(01)09521234543213",
                                "Variante para productos muy pequeños con un solo escaneo direccional."),
    "databarstacked": TypeInfo("databarstacked", "GS1 DataBar Apilado", "GS1 DataBar",
                                "(01)09521234543213", "(01)09521234543213",
                                "Igual que el Omnidireccional pero en dos filas, para etiquetas angostas."),
    "databartruncated": TypeInfo("databartruncated", "GS1 DataBar Truncado", "GS1 DataBar",
                                  "(01)09521234543213", "(01)09521234543213",
                                  "Versión de altura reducida del DataBar Omnidireccional."),

    # Códigos ISBN
    "isbn": TypeInfo("isbn", "ISBN", "Códigos ISBN",
                      "978-0-306-40615-7", "978-0-306-40615-7 (con guiones)",
                      "13 dígitos con guiones en los grupos estándar. Identifica libros publicados."),
    "issn": TypeInfo("issn", "ISSN", "Códigos ISBN",
                      "0317-8471", "0317-8471 (con el guion central)",
                      "8 dígitos con guion en medio, identifica publicaciones periódicas (revistas)."),
    "ismn": TypeInfo("ismn", "ISMN", "Códigos ISBN",
                      "M-2306-7118-7", "M-2306-7118-7 (empieza con M-)",
                      "Identifica partituras musicales impresas."),

    # Códigos de sanidad
    "pzn": TypeInfo("pzn", "PZN (Pharmazentralnummer)", "Códigos de sanidad",
                     "123456", "123456 (6 dígitos, el de control se calcula solo)",
                     "Identificador de medicamentos en Alemania."),
    "pharmacode": TypeInfo("pharmacode", "Pharmacode", "Códigos de sanidad",
                            "123456", "123456",
                            "Código binario para control de empaques farmacéuticos (no lleva datos legibles, solo un número de control)."),
    "code32": TypeInfo("code32", "Pharmacode Italiano (Code 32)", "Códigos de sanidad",
                        "12345678", "12345678 (8 dígitos)",
                        "Identificador de medicamentos usado en Italia."),

    # Códigos 2D
    "datamatrix": TypeInfo("datamatrix", "Data Matrix", "Códigos 2D",
                            "https://intelliqr.app", "https://intelliqr.app",
                            "Código 2D compacto, muy usado para marcar piezas pequeñas."),
    "pdf417": TypeInfo("pdf417", "PDF417", "Códigos 2D",
                        "https://intelliqr.app", "https://intelliqr.app",
                        "Código apilado usado en licencias de conducir y documentos de embarque."),
    "azteccode": TypeInfo("azteccode", "Código Aztec", "Códigos 2D",
                           "https://intelliqr.app", "https://intelliqr.app",
                           "Usado en boletos de tren/avión; no necesita zona de silencio grande."),
    "maxicode": TypeInfo("maxicode", "MaxiCode", "Códigos 2D",
                          "https://intelliqr.app", "https://intelliqr.app",
                          "Código circular usado por UPS para clasificación de paquetes."),
    "micropdf417": TypeInfo("micropdf417", "MicroPDF417", "Códigos 2D",
                             "https://intelliqr.app", "https://intelliqr.app",
                             "Versión reducida de PDF417 para espacios muy pequeños."),

    # Códigos GS1 2D
    "gs1datamatrix": TypeInfo("gs1datamatrix", "GS1 Data Matrix", "Códigos GS1 2D",
                               "(01)04006381333931(17)221231", "(01)04006381333931(17)221231",
                               "Data Matrix con identificadores de aplicación GS1, usado en salud y trazabilidad."),
    "gs1qrcode": TypeInfo("gs1qrcode", "GS1 QR Code", "Códigos GS1 2D",
                           "(01)04006381333931(17)221231", "(01)04006381333931(17)221231",
                           "QR con identificadores de aplicación GS1 (GS1 Digital Link)."),

    # Códigos postales
    "auspost": TypeInfo("auspost", "Australia Post 4-State", "Códigos postales",
                         "5956439111ABA", "5956439111ABA",
                         "Código postal australiano: FCC + código postal + datos del cliente."),
    "daft": TypeInfo("daft", "DAFT (simbología 4 estados)", "Códigos postales",
                      "FATDAFTDAD", "FATDAFTDAD",
                      "Solo con letras D, A, F, T — cada una representa una barra alta/baja/ascendente/descendente."),
    "japanpost": TypeInfo("japanpost", "Correo de Japón (cliente)", "Códigos postales",
                           "6540123", "6540123",
                           "Código postal japonés de 7 dígitos, opcionalmente con número de dirección."),
    "kix": TypeInfo("kix", "KIX (Correos Países Bajos)", "Códigos postales",
                     "1231FZ13", "1231FZ13",
                     "Código postal holandés (4 dígitos + 2 letras) más número de casa."),
    "planet": TypeInfo("planet", "Planet Code", "Códigos postales",
                        "40123456789", "40123456789 (11 o 13 dígitos)",
                        "Usado antiguamente por USPS para rastreo de correo saliente."),
    "postnet": TypeInfo("postnet", "USPS POSTNET", "Códigos postales",
                         "552134567", "552134567 (5, 9 u 11 dígitos)",
                         "Código postal estadounidense clásico (ZIP, ZIP+4 o ZIP+6)."),
    "royalmail": TypeInfo("royalmail", "Royal Mail 4-State", "Códigos postales",
                           "AB1234567890", "AB1234567890",
                           "Código postal del Reino Unido: código postal + número de casa."),
    "onecode": TypeInfo("onecode", "USPS Intelligent Mail", "Códigos postales",
                         "01234567094987654321", "01234567094987654321 (20 o 25 dígitos)",
                         "Sucesor moderno de POSTNET/PLANET en EE.UU."),
}

# Categorías en el orden en que deben aparecer en el selector
CATEGORIES: dict[str, list[str]] = {}
for _type_id, _info in TYPES.items():
    CATEGORIES.setdefault(_info.category, []).append(_type_id)

DISPLAY_NAMES = {tid: info.display_name for tid, info in TYPES.items()}


TWO_D_TYPES = {"datamatrix", "pdf417", "azteccode", "maxicode", "micropdf417",
               "gs1datamatrix", "gs1qrcode"}
# Alias retro-compatible usado por pantallas existentes
_2D_TYPES = TWO_D_TYPES


def _clean_bwipp_error(message: str) -> str:
    """BWIPP devuelve errores como 'bwipp.ean13badLength EAN-13 must be...'.
    Nos quedamos solo con la parte legible para el usuario."""
    text = str(message)
    if text.startswith("bwipp."):
        parts = text.split(" ", 1)
        text = parts[1] if len(parts) > 1 else text
    return text[0].upper() + text[1:] if text else "No pudimos generar el código."


@dataclass
class BarcodeGenerationResult:
    image: Image.Image


class BarcodeGenerator:
    def generate(self, barcode_type: str, value: str, show_text: bool = True, scale: int = 2) -> BarcodeGenerationResult:
        info = TYPES.get(barcode_type)
        if info is None:
            raise ValueError("Tipo de código no soportado.")
        if not value.strip():
            raise ValueError("Introduce un contenido para generar el código.")

        options: dict = {}
        if barcode_type not in TWO_D_TYPES:
            options["includetext"] = show_text

        # Antes de generar, nos aseguramos de que Ghostscript sea localizable
        # (empaquetado junto a la app, instalado en una ruta típica, o en el
        # PATH). Sin esto, en un .exe distribuido todos los códigos de barra
        # fallaban porque Ghostscript nunca está en el PATH de una máquina
        # que no lo instaló manualmente.
        ensure_ghostscript_on_path()

        try:
            image = treepoem.generate_barcode(barcode_type=info.bwipp_type, data=value, options=options,
                                               scale=max(1, min(scale, 10)))
        except FileNotFoundError as exc:
            raise ValueError(ghostscript_missing_hint()) from exc
        except treepoem.TreepoemError as exc:
            # El propio treepoem avisa así cuando no puede ubicar el binario
            # de Ghostscript (no es un FileNotFoundError, así que antes esta
            # rama nunca lo distinguía de un error real de BWIPP).
            if "ghostscript" in str(exc).lower():
                raise ValueError(ghostscript_missing_hint()) from exc
            raise ValueError(_clean_bwipp_error(exc)) from exc
        except Exception as exc:
            raise ValueError(_clean_bwipp_error(exc)) from exc

        return BarcodeGenerationResult(image=image.convert("RGB"))
