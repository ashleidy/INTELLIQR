# IntelliQR

Generador gratuito de **códigos QR estáticos** y **códigos de barras**, hecho con Streamlit. Sin cuentas y sin guardar datos: todo se genera en el momento.

## Funciones

- **Crear QR**: URL, texto, WiFi, vCard, evento, email, teléfono, SMS, WhatsApp, ubicación y SEPA. Diseño personalizable (patrón, color, logo, marco) y descarga en PNG, JPG, SVG o PDF.
- **Códigos de barras**: Code 128, Code 39, EAN-13, EAN-8, UPC-A e ITF-14.
- **Escáner**: sube una imagen y lee el código.

## Ejecutar en local

```bash
git clone https://github.com/ashleidy/INTELLIQR.git
cd INTELLIQR
python -m venv .venv
.venv\Scripts\activate        # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

Se abre en http://localhost:8501.

Para los códigos de barras instala además **Ghostscript** (ghostscript.com en Windows, `brew install ghostscript zbar` en Mac, `sudo apt install ghostscript libzbar0` en Linux). El QR funciona sin él.

## Publicar en Streamlit Cloud

1. Entra a [share.streamlit.io](https://share.streamlit.io) con GitHub.
2. **Create app** → repositorio `ashleidy/INTELLIQR`, rama `main`, archivo `app.py`.
3. **Deploy**. No necesita secretos; `packages.txt` instala Ghostscript y zbar.

## Estructura

```
app.py            # entrada y navegación
pages/            # Crear QR, Códigos de barras, Escáner
services/         # lógica de QR y códigos de barras
utils/            # configuración y componentes
intelliqr/        # motor de generación y escaneo
packages.txt      # dependencias del sistema (Streamlit Cloud)
requirements.txt  # dependencias de Python
```

---

*Developed by Ashleidy*
