from __future__ import annotations

from io import BytesIO

import streamlit as st

from utils.helpers import bootstrap_legacy_path

from utils.i18n import tr

bootstrap_legacy_path()

st.title(tr("Escáner"))
st.caption(tr("Sube una foto o captura de un código y léelo al instante."))

try:
    from PIL import Image
    from core.scan_engine.scanner import Scanner, classify_action

    scanner_disponible = True
except Exception:  # noqa: BLE001
    scanner_disponible = False

if not scanner_disponible:
    st.error(tr(
        "El motor de escaneo no está disponible en este entorno. Necesita la "
        "librería del sistema `libzbar0` (se instala vía `packages.txt` en "
        "Streamlit Cloud)."
    ))
    st.stop()

archivo = st.file_uploader(
    tr("Imagen del código"), type=["png", "jpg", "jpeg", "webp", "bmp"]
)

if archivo is None:
    st.info(tr("Sube una imagen para empezar."))
    st.stop()

try:
    imagen = Image.open(BytesIO(archivo.getvalue()))
except Exception:  # noqa: BLE001
    st.error(tr("No fue posible abrir esa imagen."))
    st.stop()

col_img, col_res = st.columns([2, 3], gap="large")
with col_img:
    st.image(imagen, width="stretch")

with col_res:
    resultados = Scanner().decode(imagen)
    if not resultados:
        st.warning(tr(
            "No se detectó ningún código. Prueba con una imagen más nítida, "
            "mejor iluminada o recortada alrededor del código."
        ))
        st.caption(tr(
            "Nota: zbar lee QR y códigos lineales (EAN, UPC, Code 128, Code 39, "
            "Codabar, ITF), pero no Data Matrix, PDF417 ni Aztec."
        ))
    else:
        for index, resultado in enumerate(resultados):
            with st.container(border=True):
                st.markdown(f"**{tr(resultado.type_label)}**")
                st.code(resultado.content, language=None)
                enlace = classify_action(resultado.content)
                if enlace:
                    st.link_button(tr("Abrir"), enlace, width="stretch")

