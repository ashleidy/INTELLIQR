# IntelliQR

Aplicación de escritorio (Windows) para crear, personalizar, guardar, imprimir
y exportar códigos QR estáticos, códigos de barras y etiquetas.
Aplicación **gratuita**, sin licencias ni activación, y sin dependencia
de internet para el uso diario.

## Estado actual (V1 — Fases 1 a 5 del roadmap)

Implementado y probado:

- ✅ App base con sidebar, pantalla de inicio y navegación (Fase 1)
- ✅ Todos los tipos de QR del spec: URL, Google Maps, WhatsApp, Teléfono, SMS,
  Email, VCard, Texto, WiFi, Evento, Ubicación (Fase 2)
- ✅ Motor central `QRGenerator` (payload → matriz → personalización), sin
  duplicar lógica por tipo (sección 42)
- ✅ Diseñador: patrón, esquinas, color, degradado, logo (con aviso si tapa
  demasiado el QR), marcos con texto (Fase 3)
- ✅ Vista previa en tiempo real en cada paso (contenido y diseño)
- ✅ Exportación PNG (300/600 DPI), JPG, SVG vectorial y PDF listo para
  imprimir, más impresión directa vía diálogo del sistema (Fase 4)
- ✅ Guardar/listar/duplicar/eliminar proyectos en SQLite local (Fase 5,
  base de "Mis QR")
- ✅ **Abrir desde "Mis QR" y "Recientes"** el último QR (o cualquiera)
  ya guardado, con opción de volver atrás a editar contenido/diseño sin
  duplicar el registro
- ✅ **Códigos de barras**: catálogo casi completo de tec-it.com (~39 tipos)
  vía BWIPP/Ghostscript — Códigos lineales (Code128, Code39, Code93,
  Codabar, ITF, MSI, GS1-128), EAN/UPC, **GS1 DataBar** (5 variantes),
  ISBN/ISSN/ISMN, Sanidad (PZN, Pharmacode, Code 32), **2D** (Data Matrix,
  PDF417, Aztec, MaxiCode, MicroPDF417), **GS1 2D** (GS1 Data Matrix, GS1
  QR), y **Códigos postales** (Australia Post, DAFT, Japan Post, KIX,
  Planet, POSTNET, Royal Mail 4-State, USPS Intelligent Mail). Cada tipo
  muestra ayuda y un ejemplo real que se puede insertar con un clic (Fase 7)
- ✅ **Escáner** de QR y códigos de barras con cámara en vivo (recuadro
  de detección en tiempo real) o cargando una imagen, con acciones
  Copiar/Abrir/Guardar e historial en base de datos (Fase 11)
- ✅ **Imprimir**: elige un QR o código de barras guardado (o carga una
  imagen), configura tamaño de papel (A4/Carta/Personalizado),
  orientación, margen, tamaño de cada copia y cantidad — calcula
  automáticamente cuántas copias caben por página (cuadrícula) y en
  cuántas páginas, con vista previa nativa antes de imprimir
- ✅ **Configuración**: tamaño de letra (Pequeño/Normal/Grande/Muy
  grande, aplicado al instante a toda la app) e idioma Español/Inglés
  (aplicado al instante en la barra lateral, inicio y esta misma
  pantalla — ver nota de alcance abajo), ambos guardados y recordados
  entre sesiones

- ✅ Identidad visual propia (azul #2563EB, tipografía Segoe UI, tarjetas
  limpias) — sin ningún elemento de QR.io
- ✅ 51 tests unitarios cubriendo validación, payloads, exportación,
  las ~39 simbologías de código de barras, el round-trip de escaneo,
  el motor de impresión y el sistema de idioma

No se incluyen (no existe una librería Python confiable para generarlos
correctamente, y preferimos dejarlos fuera antes que una implementación
casera sin verificar): **DPD Parcel Label** y el código de la **Autoridad
Postal Coreana**.



**Alcance actual de la traducción al inglés**: por el enorme volumen de
texto que ya tiene la app (formularios de cada tipo de QR, ayuda de los
~39 códigos de barras, etc.), esta primera versión traduce el "chrome"
permanente — barra lateral, inicio y la propia pantalla de Configuración
— de forma real y verificada (no es una promesa: el interruptor cambia
el texto al instante). El resto de pantallas (crear QR, códigos de
barras, escáner, imprimir) siguen en español por ahora; se pueden ir
sumando al diccionario en `ui/i18n.py` progresivamente, pantalla por
pantalla, sin tocar la lógica de negocio.

Pendiente (si se retoma en el futuro):

- ⏳ Instalador Windows con PyInstaller + Inno Setup (Fase 13)

## ⚠️ Requisito adicional: Ghostscript

El motor de códigos de barras (BWIPP) necesita **Ghostscript** instalado
en el sistema — es gratuito y de código abierto, pero **no se instala con
pip**, es un programa aparte.

**En Windows:**
1. Descarga el instalador de https://www.ghostscript.com/releases/gsdnld.html
   (elige "Ghostscript for Windows (64 bit)").
2. Instálalo con las opciones por defecto.
3. Reinicia la terminal / VS Code para que reconozca el nuevo programa.

Si `treepoem` no encuentra Ghostscript, la app muestra un mensaje amigable
con este mismo enlace en lugar de fallar con un error técnico. El resto de
la app (QR, escáner) funciona sin este requisito — solo lo necesita el
módulo de códigos de barras.

## Instalación (desarrollo)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app/main.py
```

## Ejecutar los tests

```bash
pip install pytest
pytest tests/ -v
```

## Generar el ejecutable (cuando llegue la Fase 13)

```bash
pyinstaller --name IntelliQR --windowed --onefile app/main.py
```
(Luego empaquetar con Inno Setup para crear `IntelliQR-Setup.exe`. El
instalador de Inno Setup también deberá incluir o exigir Ghostscript.)

## Notas técnicas importantes

- **SVG de código de barras**: ya no está disponible — BWIPP entrega
  únicamente imagen rasterizada (PNG/PDF), suficiente calidad para
  escanear e imprimir. El SVG del propio QR (no de códigos de barras)
  sigue disponible sin cambios.
- **SVG del QR**: por limitaciones de las librerías de estilizado de
  `qrcode`, el SVG exportado es el QR base vectorial (sin logo ni
  degradado). Es 100% escaneable y perfecto para imprenta a cualquier
  tamaño. El PNG/PDF sí incluyen todo el diseño.
- **Corrección de errores**: se usa automáticamente nivel `H` cuando hay
  logo, `M` en el resto, respetando siempre una zona de silencio mínima.
- **Escáner / pyzbar en Windows**: `pyzbar` necesita la librería `zbar`;
  en Windows el paquete de PyPI ya incluye el DLL necesario, así que
  `pip install pyzbar` debería bastar. Si el escáner no detecta nada,
  confirma que la cámara no esté siendo usada por otra app (Zoom, Teams,
  etc.) — Windows solo permite un programa a la vez usándola. Además,
  el escáner (zbar) NO puede leer Data Matrix, PDF417 ni Aztec — solo
  detecta QR y los códigos lineales/EAN/UPC/GS1 DataBar.
- **Arquitectura**: sigue exactamente la carpeta propuesta en el
  documento de especificación (`app/`, `ui/`, `core/`, `qr_types/`,
  `database/`), con separación estricta entre lógica de negocio e interfaz.
