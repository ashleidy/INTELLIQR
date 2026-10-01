"""Escáner: decodifica QR y códigos de barras desde una imagen subida.

Se reutiliza `intelliqr/core/scan_engine/scanner.py` sin cambios. Lo que NO
se migró es la captura de vídeo en vivo con OpenCV: un bucle de cámara no
tiene equivalente razonable en Streamlit sin dependencias extra, y la
decodificación —que es la parte con valor— es idéntica.
"""
from __future__ import annotations

from io import BytesIO

import streamlit as st

from utils.helpers import bootstrap_legacy_path

bootstrap_legacy_path()

st.title("Escáner")
st.caption("Sube una foto o captura de un código y léelo al instante.")

try:
    from PIL import Image
    from core.scan_engine.scanner import Scanner, classify_action

    scanner_disponible = True
except Exception:  # noqa: BLE001
    scanner_disponible = False

if not scanner_disponible:
    st.error(
        "El motor de escaneo no está disponible en este entorno. Necesita la "
        "librería del sistema `libzbar0` (se instala vía `packages.txt` en "
        "Streamlit Cloud)."
    )
    st.stop()

archivo = st.file_uploader(
    "Imagen del código", type=["png", "jpg", "jpeg", "webp", "bmp"]
)

if archivo is None:
    st.info("Sube una imagen para empezar.")
    st.stop()

try:
    imagen = Image.open(BytesIO(archivo.getvalue()))
except Exception:  # noqa: BLE001
    st.error("No fue posible abrir esa imagen.")
    st.stop()

col_img, col_res = st.columns([2, 3], gap="large")
with col_img:
    st.image(imagen, width="stretch")

with col_res:
    resultados = Scanner().decode(imagen)
    if not resultados:
        st.warning(
            "No se detectó ningún código. Prueba con una imagen más nítida, "
            "mejor iluminada o recortada alrededor del código."
        )
        st.caption(
            "Nota: zbar lee QR y códigos lineales (EAN, UPC, Code 128, Code 39, "
            "Codabar, ITF), pero no Data Matrix, PDF417 ni Aztec."
        )
    else:
        for index, resultado in enumerate(resultados):
            with st.container(border=True):
                st.markdown(f"**{resultado.type_label}**")
                st.code(resultado.content, language=None)
                enlace = classify_action(resultado.content)
                if enlace:
                    st.link_button("Abrir", enlace, width="stretch")
