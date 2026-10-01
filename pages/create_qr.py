"""Crear QR — solo códigos QR estáticos (URL, WiFi, vCard, evento, SEPA…).

Herramienta pública: no hay cuentas ni historial. El código se genera en la
sesión del visitante y se descarga; nada se almacena en el servidor.
"""
from __future__ import annotations

import streamlit as st

from services.qr_service import (
    build_qr_image, build_static_payload, get_form_schema,
    list_static_categories, validate_static_content,
)
from utils.ui_components import design_controls, download_row

st.title("Crear QR")
st.caption("Genera un código QR estático y descárgalo gratis. No guardamos tus datos.")

col_form, col_preview = st.columns([5, 4], gap="large")

with col_form:
    st.subheader("1. Contenido")

    categorias = list_static_categories()
    categoria = st.selectbox("Categoría", list(categorias.keys()))
    qr_type = st.selectbox("Tipo de QR", categorias[categoria],
                           format_func=lambda t: t.display_name)
    st.caption(qr_type.description)
    tipo = qr_type.type_id

    data: dict = {}
    for field in get_form_schema(tipo):
        label = field.label + ("" if field.required else " (opcional)")
        widget_key = f"static_{tipo}_{field.key}"
        if field.kind == "textarea":
            data[field.key] = st.text_area(label, placeholder=field.placeholder, key=widget_key)
        elif field.kind == "select":
            data[field.key] = st.selectbox(label, field.options, key=widget_key)
        elif field.kind == "checkbox":
            data[field.key] = st.checkbox(label, value=bool(field.default), key=widget_key)
        else:
            data[field.key] = st.text_input(label, placeholder=field.placeholder, key=widget_key)

    payload: str | None = None
    errores: list[str] = []
    if any(str(v).strip() for v in data.values()):
        result = validate_static_content(tipo, data)
        if result.is_valid:
            payload = build_static_payload(tipo, data)
        else:
            errores = list(result.errors.values())

    nombre_archivo = st.text_input("Nombre del archivo (opcional)", placeholder="mi-qr")

    st.subheader("2. Diseño")
    design, logo_file = design_controls("create")

with col_preview:
    st.subheader("Vista previa")
    if payload:
        try:
            image, warnings = build_qr_image(payload, design, logo_bytes=logo_file)
            st.image(image, width="stretch")
            for warning in warnings:
                st.warning(warning)
            download_row(image, payload, nombre_archivo.strip() or "qr", "create")
        except ValueError as exc:
            st.error(str(exc))
        except Exception:  # noqa: BLE001
            st.error("No fue posible generar el código con estas opciones.")
    else:
        st.info("Completa el contenido para ver la vista previa.")

for error in errores:
    st.error(error)
