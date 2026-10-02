
from __future__ import annotations

import re
import unicodedata

import streamlit as st

LANGS = {"es": "Español", "en": "English"}


def current_lang() -> str:
    lang = st.session_state.get("lang", "es")
    return lang if lang in LANGS else "es"


EN: dict[str, str] = {
    # ---------------------------------------------------------------- app
    "IntelliQR — QR estático y códigos de barras": "IntelliQR — Static QR & barcodes",
    "Generador de QR estático": "Static QR generator",
    "🔒 No guardamos tus datos: todo se genera en el momento.":
        "🔒 We don't store your data: everything is generated on the spot.",
    "Crear QR": "Create QR",
    "Códigos de barras": "Barcodes",
    "Escáner": "Scanner",
    "Idioma": "Language",
    # ---------------------------------------------------------- crear QR
    "Genera un código QR estático y descárgalo gratis. No guardamos tus datos.":
        "Generate a static QR code and download it for free. We don't store your data.",
    "1. Contenido": "1. Content",
    "2. Diseño": "2. Design",
    "Categoría": "Category",
    "Tipo de QR": "QR type",
    "(opcional)": "(optional)",
    "Nombre del archivo (opcional)": "File name (optional)",
    "mi-qr": "my-qr",
    "Vista previa": "Preview",
    "Completa el contenido para ver la vista previa.": "Fill in the content to see the preview.",
    "No fue posible generar el código con estas opciones.":
        "The code could not be generated with these options.",
    # ------------------------------------------------- campos de formularios
    "URL": "URL", "Dirección": "Address", "URL de Google Maps (opcional)": "Google Maps URL (optional)",
    "Código de país": "Country code", "Número": "Number", "Mensaje predefinido": "Pre-filled message",
    "Mensaje": "Message", "Correo electrónico": "Email address", "Asunto": "Subject",
    "Nombre": "First name", "Apellido": "Last name", "Empresa": "Company", "Cargo": "Job title",
    "Teléfono": "Phone", "Móvil": "Mobile", "Email": "Email", "Sitio web": "Website",
    "Ciudad": "City", "País": "Country", "Texto": "Text",
    "Nombre de red (SSID)": "Network name (SSID)", "Contraseña": "Password",
    "Tipo de seguridad": "Security type", "Red oculta": "Hidden network",
    "Sin contraseña": "No password",
    "Nombre del evento": "Event name", "Fecha (AAAA-MM-DD)": "Date (YYYY-MM-DD)",
    "Hora (HH:MM)": "Time (HH:MM)", "Ubicación": "Location", "Descripción": "Description",
    "URL relacionada": "Related URL", "Latitud": "Latitude", "Longitud": "Longitude",
    "Nombre del beneficiario": "Beneficiary name", "BIC / SWIFT (opcional)": "BIC / SWIFT (optional)",
    "Monto en EUR (opcional)": "Amount in EUR (optional)",
    "Referencia estructurada (opcional)": "Structured reference (optional)",
    "Concepto (opcional)": "Purpose (optional)",
    # placeholders con texto en español
    "https://tusitio.com": "https://yoursite.com", "Calle 123, Ciudad": "123 Main St, City",
    "Hola, quiero más información...": "Hi, I'd like more information...",
    "Escribe el mensaje...": "Write the message...", "Escribe el contenido...": "Write the content...",
    "correo@ejemplo.com": "email@example.com", "Juan": "John", "Pérez": "Smith",
    "MiRedWiFi": "MyWiFi", "Lanzamiento de producto": "Product launch", "Empresa S.A.S.": "Company Inc.",
    # ----------------------------------------- mensajes de validación (motor)
    "Introduce un correo electrónico válido.": "Enter a valid email address.",
    "Introduce el nombre del evento.": "Enter the event name.",
    "Introduce la fecha del evento (AAAA-MM-DD).": "Enter the event date (YYYY-MM-DD).",
    "La fecha debe tener el formato AAAA-MM-DD.": "The date must use the format YYYY-MM-DD.",
    "Introduce coordenadas numéricas válidas.": "Enter valid numeric coordinates.",
    "La latitud debe estar entre -90 y 90.": "Latitude must be between -90 and 90.",
    "La longitud debe estar entre -180 y 180.": "Longitude must be between -180 and 180.",
    "Introduce una dirección, coordenadas o una URL de Maps.": "Enter an address, coordinates or a Maps URL.",
    "Introduce un código de país válido.": "Enter a valid country code.",
    "Introduce un número de teléfono válido.": "Enter a valid phone number.",
    "Introduce el nombre del beneficiario.": "Enter the beneficiary name.",
    "El nombre no puede superar los 70 caracteres.": "The name cannot exceed 70 characters.",
    "Introduce un IBAN válido, ej. ES9121000418450200051332.": "Enter a valid IBAN, e.g. ES9121000418450200051332.",
    "El monto debe ser un número positivo, ej. 25.50.": "The amount must be a positive number, e.g. 25.50.",
    "Introduce un texto.": "Enter some text.",
    "Introduce una URL.": "Enter a URL.",
    "Introduce una URL válida (debe comenzar con http:// o https://).":
        "Enter a valid URL (it must start with http:// or https://).",
    "Introduce al menos el nombre.": "Enter at least the first name.",
    "Introduce el nombre de la red (SSID).": "Enter the network name (SSID).",
    "Introduce la contraseña de la red.": "Enter the network password.",
    "El contenido es demasiado extenso para un código QR. Intenta acortarlo.":
        "The content is too long for a QR code. Try shortening it.",
    "El logo es demasiado grande y puede afectar la lectura del código.":
        "The logo is too large and may affect how well the code scans.",
    # ----------------------------------------------------- diseño (widgets)
    "Básico": "Basic", "Color": "Color", "Logo": "Logo", "Marco": "Frame",
    "Patrón de módulos": "Module pattern", "Tamaño del módulo (px)": "Module size (px)",
    "Cuanto mayor, más grande sale la imagen generada.": "The larger it is, the bigger the generated image.",
    "Margen / zona de silencio": "Margin / quiet zone",
    "Nunca baja de 2: sin zona de silencio, muchos lectores fallan.":
        "Never below 2: without a quiet zone, many scanners fail.",
    "Fondo transparente (PNG/SVG)": "Transparent background (PNG/SVG)",
    "No se aplica si usas degradado.": "Not applied when using a gradient.",
    "Color del código": "Code color", "Color de fondo": "Background color",
    "Usar degradado": "Use gradient", "Degradado — inicio": "Gradient — start",
    "Degradado — fin": "Gradient — end", "Dirección del degradado": "Gradient direction",
    "Mantén suficiente contraste entre código y fondo: un QR claro sobre fondo claro puede dejar de leerse.":
        "Keep enough contrast between code and background: a light QR on a light background may stop scanning.",
    "Logo (PNG, JPG o SVG rasterizado)": "Logo (PNG, JPG or rasterized SVG)",
    "Tamaño del logo": "Logo size",
    "Con logo, la corrección de errores sube automáticamente a nivel H para compensar la zona cubierta.":
        "With a logo, error correction automatically rises to level H to compensate for the covered area.",
    "Estilo de marco": "Frame style", "Texto del marco": "Frame text", "Color del marco": "Frame color",
    "Color del texto": "Text color", "Grosor del marco": "Frame thickness", "Tamaño del texto": "Text size",
    "Cuadrado": "Square", "Redondeado": "Rounded", "Puntos": "Dots", "Suave": "Soft", "Moderno": "Modern",
    "Sin marco": "No frame", "Banda inferior": "Bottom band", "Banda superior": "Top band",
    "Etiqueta": "Label", "Promocional": "Promotional", "Circular": "Circular",
    "Navegador": "Browser", "Bolsa": "Bag",
    "ESCANÉAME": "SCAN ME",
    # ------------------------------------------------------------ descargas
    "Tamaño de impresión": "Print size", "Original": "Original", "Pequeño": "Small",
    "Mediano": "Medium", "Grande": "Large", "Personalizado": "Custom",
    "Ancho (cm)": "Width (cm)", "Alto (cm)": "Height (cm)",
    "El SVG es el QR base vectorial (sin logo ni degradado), ideal para imprenta. PNG y PDF incluyen todo el diseño.":
        "The SVG is the base vector QR (no logo or gradient), ideal for printing. PNG and PDF include the full design.",
    # ------------------------------------------------------ códigos de barras
    "Genera los formatos más comunes y descárgalos en PNG.": "Generate the most common formats and download them as PNG.",
    "El motor de códigos de barras no está disponible en este entorno. Comprueba que `treepoem` esté en requirements.txt y que Ghostscript esté instalado (en Streamlit Cloud llega vía `packages.txt`).":
        "The barcode engine is not available in this environment. Check that `treepoem` is in requirements.txt and that Ghostscript is installed (on Streamlit Cloud it comes via `packages.txt`).",
    "Tipo de código": "Code type", "Contenido": "Content", "Ejemplo": "Example",
    "Mostrar texto legible": "Show human-readable text",
    "Introduce un contenido para ver la vista previa.": "Enter some content to see the preview.",
    "Introduce un contenido para generar el código.": "Enter some content to generate the code.",
    "Descargar PNG": "Download PNG",
    "No fue posible generar el código. Revisa el contenido e intenta nuevamente.":
        "The code could not be generated. Check the content and try again.",
    "Acepta letras, números y símbolos. El más usado en logística e inventario.":
        "Accepts letters, numbers and symbols. The most used in logistics and inventory.",
    "Letras mayúsculas, números y algunos símbolos (- . espacio $ / + %).":
        "Uppercase letters, numbers and some symbols (- . space $ / + %).",
    "El código de barras estándar de productos de retail en Europa/LatAm.":
        "The standard retail product barcode in Europe/LatAm.",
    "Versión reducida de EAN-13 para envases pequeños.": "Short version of EAN-13 for small packages.",
    "El estándar de retail en EE.UU. y Canadá.": "The retail standard in the US and Canada.",
    "Para unidades logísticas (cajas, pallets). 14 dígitos en el código final.":
        "For logistic units (boxes, pallets). 14 digits in the final code.",
    "PRODUCTO-00123": "PRODUCT-00123",
    "400638133393 (12 dígitos, el de control se calcula solo)": "400638133393 (12 digits, the check digit is calculated automatically)",
    "9638507 (7 dígitos, el de control se calcula solo)": "9638507 (7 digits, the check digit is calculated automatically)",
    "03600029145 (11 dígitos, el de control se calcula solo)": "03600029145 (11 digits, the check digit is calculated automatically)",
    "1234567890123 (13 dígitos, el de control se calcula solo)": "1234567890123 (13 digits, the check digit is calculated automatically)",
    "Este tipo de código necesita Ghostscript instalado en el sistema (es gratuito). Descárgalo de https://www.ghostscript.com/releases/gsdnld.html y vuelve a intentarlo.":
        "This code type needs Ghostscript installed on the system (it's free). Download it from https://www.ghostscript.com/releases/gsdnld.html and try again.",
    # --------------------------------------------------------------- escáner
    "Sube una foto o captura de un código y léelo al instante.": "Upload a photo or screenshot of a code and read it instantly.",
    "El motor de escaneo no está disponible en este entorno. Necesita la librería del sistema `libzbar0` (se instala vía `packages.txt` en Streamlit Cloud).":
        "The scanning engine is not available in this environment. It needs the system library `libzbar0` (installed via `packages.txt` on Streamlit Cloud).",
    "Imagen del código": "Code image", "Sube una imagen para empezar.": "Upload an image to get started.",
    "No fue posible abrir esa imagen.": "That image could not be opened.",
    "No se detectó ningún código. Prueba con una imagen más nítida, mejor iluminada o recortada alrededor del código.":
        "No code detected. Try a sharper, better-lit image, or crop it around the code.",
    "Nota: zbar lee QR y códigos lineales (EAN, UPC, Code 128, Code 39, Codabar, ITF), pero no Data Matrix, PDF417 ni Aztec.":
        "Note: zbar reads QR and linear codes (EAN, UPC, Code 128, Code 39, Codabar, ITF), but not Data Matrix, PDF417 or Aztec.",
    "Abrir": "Open", "Código QR": "QR code",
}


def tr(text: str) -> str:
    """Traduce `text` (escrito en español) al idioma activo."""
    if current_lang() == "es" or not text:
        return text
    return EN.get(text, text)


def _slug(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", plain.lower()).strip("_")


def _legacy_en() -> dict[str, str]:
    """Traducciones ya hechas para la app de escritorio (solo lectura)."""
    try:
        from ui.i18n import TRANSLATIONS  # intelliqr/ui/i18n.py

        return TRANSLATIONS.get("en", {})
    except Exception:  # noqa: BLE001
        return {}


def category_label(name: str) -> str:
    if current_lang() == "es":
        return name
    return _legacy_en().get(f"category.{_slug(name)}", name)


def qr_type_name(type_id: str, fallback: str) -> str:
    if current_lang() == "es":
        return fallback
    return _legacy_en().get(f"qrtype.{type_id}.name", fallback)


def qr_type_desc(type_id: str, fallback: str) -> str:
    if current_lang() == "es":
        return fallback
    return _legacy_en().get(f"qrtype.{type_id}.desc", fallback)


_MAX_RE = re.compile(r"El texto supera el máximo de (\d+) caracteres\.")


def tr_msg(text: str) -> str:
    """Igual que tr(), pero también cubre mensajes con números."""
    if current_lang() == "es":
        return text
    match = _MAX_RE.fullmatch(text)
    if match:
        return f"The text exceeds the maximum of {match.group(1)} characters."
    return tr(text)


def language_selector() -> None:
    """Selector ES/EN para la barra lateral."""
    st.radio(
        "🌐", list(LANGS), format_func=LANGS.get, horizontal=True,
        key="lang", label_visibility="collapsed",
    )
