"""Códigos de barras — solo las simbologías esenciales."""
from __future__ import annotations

import streamlit as st

from services import barcode_service
from services.barcode_service import BarcodeUnavailable
from utils.helpers import safe_filename

st.title("Códigos de barras")
st.caption("Genera los formatos más comunes y descárgalos en PNG.")

if not barcode_service.ENGINE_AVAILABLE:
    st.error(
        "El motor de códigos de barras no está disponible en este entorno. "
        "Comprueba que `treepoem` esté en requirements.txt y que Ghostscript "
        "esté instalado (en Streamlit Cloud llega vía `packages.txt`)."
    )
    st.stop()

col_form, col_preview = st.columns([5, 4], gap="large")

with col_form:
    type_id = st.selectbox(
        "Tipo de código", barcode_service.list_types(),
        format_func=barcode_service.display_name,
    )
    info = barcode_service.type_info(type_id)
    st.caption(info.help_text)

    valor = st.text_input("Contenido", key=f"bc_value_{type_id}", placeholder=info.placeholder)
    st.caption(f"Ejemplo: {info.example}")

    mostrar_texto = st.checkbox("Mostrar texto legible", value=True)

with col_preview:
    st.subheader("Vista previa")

    if not valor:
        st.info("Introduce un contenido para ver la vista previa.")
    else:
        error = barcode_service.validate(type_id, valor)
        if error:
            st.error(error)
        else:
            try:
                image = barcode_service.generate(type_id, valor, show_text=mostrar_texto, scale=3)
                st.image(image, width="stretch")
                st.download_button(
                    "Descargar PNG",
                    data=barcode_service.to_png_bytes(image),
                    file_name=f"{safe_filename(f'{type_id}-{valor}', 'codigo')}.png",
                    mime="image/png",
                    width="stretch",
                )
            except BarcodeUnavailable as exc:
                st.error(str(exc))
            except ValueError as exc:
                st.error(str(exc))
            except Exception:  # noqa: BLE001
                st.error("No fue posible generar el código. Revisa el contenido e intenta nuevamente.")
