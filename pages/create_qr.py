
from __future__ import annotations

import streamlit as st

from services.qr_service import (
    build_qr_image, build_static_payload, get_form_schema,
    list_static_categories, validate_static_content,
)
from utils.i18n import category_label, qr_type_desc, qr_type_name, tr, tr_msg
from utils.ui_components import design_controls, download_row

st.title(tr("Crear QR"))
st.caption(tr("Genera un código QR estático y descárgalo gratis. No guardamos tus datos."))

col_form, col_preview = st.columns([5, 4], gap="large")

with col_form:
    st.subheader(tr("1. Contenido"))

    categorias = list_static_categories()
    categoria = st.selectbox(tr("Categoría"), list(categorias.keys()), format_func=category_label)
    qr_type = st.selectbox(tr("Tipo de QR"), categorias[categoria],
                           format_func=lambda t: qr_type_name(t.type_id, t.display_name))
    st.caption(qr_type_desc(qr_type.type_id, qr_type.description))
    tipo = qr_type.type_id

    data: dict = {}
    for field in get_form_schema(tipo):
        label = tr(field.label)
        if not field.required and "(opcional)" not in field.label:
            label += " " + tr("(opcional)")
        placeholder = tr(field.placeholder)
        widget_key = f"static_{tipo}_{field.key}"
        if field.kind == "textarea":
            data[field.key] = st.text_area(label, placeholder=placeholder, key=widget_key)
        elif field.kind == "select":
            data[field.key] = st.selectbox(label, field.options, key=widget_key, format_func=tr)
        elif field.kind == "checkbox":
            data[field.key] = st.checkbox(label, value=bool(field.default), key=widget_key)
        else:
            data[field.key] = st.text_input(label, placeholder=placeholder, key=widget_key)

    payload: str | None = None
    errores: list[str] = []
    if any(str(v).strip() for v in data.values()):
        result = validate_static_content(tipo, data)
        if result.is_valid:
            payload = build_static_payload(tipo, data)
        else:
            errores = [tr_msg(m) for m in result.errors.values()]

    nombre_archivo = st.text_input(tr("Nombre del archivo (opcional)"), placeholder=tr("mi-qr"))

    st.subheader(tr("2. Diseño"))
    design, logo_file = design_controls("create")

with col_preview:
    st.subheader(tr("Vista previa"))
    if payload:
        try:
            image, warnings = build_qr_image(payload, design, logo_bytes=logo_file)
            st.image(image, width="stretch")
            for warning in warnings:
                st.warning(tr_msg(warning))
            download_row(image, payload, nombre_archivo.strip() or "qr", "create")
        except ValueError as exc:
            st.error(tr_msg(str(exc)))
        except Exception:  # noqa: BLE001
            st.error(tr("No fue posible generar el código con estas opciones."))
    else:
        st.info(tr("Completa el contenido para ver la vista previa."))

for error in errores:
    st.error(error)

