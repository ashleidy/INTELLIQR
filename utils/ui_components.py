"""Widgets reutilizables de la interfaz.

El diseñador completo (patrones, colores, degradado, logo, 10 marcos) vive
aquí una sola vez y lo usan tanto «Crear QR» como «Mis QR» al reeditar el
diseño de un código ya existente.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from services.qr_service import DesignSettings, FRAME_STYLES, PATTERNS

PATTERN_LABELS = {
    "cuadrado": "Cuadrado",
    "redondeado": "Redondeado",
    "puntos": "Puntos",
    "suave": "Suave",
    "moderno": "Moderno",
}

FRAME_LABELS = {
    "ninguno": "Sin marco",
    "simple": "Banda inferior",
    "moderno": "Banda superior",
    "redondeado": "Redondeado",
    "etiqueta": "Etiqueta",
    "promocional": "Promocional",
    "circular": "Circular",
    "telefono": "Teléfono",
    "navegador": "Navegador",
    "bolsa": "Bolsa",
}


def design_controls(key_prefix: str, initial: DesignSettings | None = None
                    ) -> tuple[DesignSettings, Any]:
    """Dibuja el diseñador completo y devuelve (diseño, logo_subido).

    El logo se mantiene en memoria: en Streamlit Cloud el disco es efímero,
    así que nunca se guarda una ruta.
    """
    d = initial or DesignSettings()

    tab_basico, tab_color, tab_logo, tab_marco = st.tabs(
        ["Básico", "Color", "Logo", "Marco"]
    )

    with tab_basico:
        col1, col2 = st.columns(2)
        with col1:
            pattern = st.selectbox(
                "Patrón de módulos", PATTERNS,
                index=PATTERNS.index(d.pattern) if d.pattern in PATTERNS else 0,
                format_func=lambda p: PATTERN_LABELS.get(p, p),
                key=f"{key_prefix}_pattern",
            )
            box_size = st.slider(
                "Tamaño del módulo (px)", 4, 20, d.box_size,
                key=f"{key_prefix}_box",
                help="Cuanto mayor, más grande sale la imagen generada.",
            )
        with col2:
            border = st.slider(
                "Margen / zona de silencio", 2, 10, max(d.border, 2),
                key=f"{key_prefix}_border",
                help="Nunca baja de 2: sin zona de silencio, muchos lectores fallan.",
            )
            transparent = st.checkbox(
                "Fondo transparente (PNG/SVG)", value=d.transparent_background,
                key=f"{key_prefix}_transparent",
                help="No se aplica si usas degradado.",
            )

    with tab_color:
        col1, col2 = st.columns(2)
        with col1:
            fg_color = st.color_picker("Color del código", d.fg_color, key=f"{key_prefix}_fg")
            bg_color = st.color_picker("Color de fondo", d.bg_color, key=f"{key_prefix}_bg")
        with col2:
            gradient_enabled = st.checkbox(
                "Usar degradado", value=d.gradient_enabled, key=f"{key_prefix}_grad"
            )
            gradient_start = st.color_picker(
                "Degradado — inicio", d.gradient_start,
                key=f"{key_prefix}_grad_start", disabled=not gradient_enabled,
            )
            gradient_end = st.color_picker(
                "Degradado — fin", d.gradient_end,
                key=f"{key_prefix}_grad_end", disabled=not gradient_enabled,
            )
            gradient_direction = st.radio(
                "Dirección", ["horizontal", "vertical"],
                index=0 if d.gradient_direction == "horizontal" else 1,
                horizontal=True, key=f"{key_prefix}_grad_dir",
                disabled=not gradient_enabled,
            )
        st.caption(
            "Mantén suficiente contraste entre código y fondo: un QR claro sobre "
            "fondo claro puede dejar de leerse."
        )

    with tab_logo:
        logo_file = st.file_uploader(
            "Logo (PNG, JPG o SVG rasterizado)", type=["png", "jpg", "jpeg", "webp"],
            key=f"{key_prefix}_logo",
        )
        logo_size_ratio = st.slider(
            "Tamaño del logo", 0.05, 0.40, float(d.logo_size_ratio), step=0.01,
            key=f"{key_prefix}_logo_ratio",
            format="%.2f",
        )
        if logo_size_ratio > 0.30:
            st.warning("El logo es demasiado grande y puede afectar la lectura del código.")
        st.caption(
            "Con logo, la corrección de errores sube automáticamente a nivel H "
            "para compensar la zona cubierta."
        )

    with tab_marco:
        frame_style = st.selectbox(
            "Estilo de marco", FRAME_STYLES,
            index=FRAME_STYLES.index(d.frame_style) if d.frame_style in FRAME_STYLES else 0,
            format_func=lambda f: FRAME_LABELS.get(f, f),
            key=f"{key_prefix}_frame",
        )
        disabled = frame_style == "ninguno"
        col1, col2 = st.columns(2)
        with col1:
            frame_text = st.text_input(
                "Texto del marco", d.frame_text, key=f"{key_prefix}_frame_text", disabled=disabled
            )
            frame_color = st.color_picker(
                "Color del marco", d.frame_color, key=f"{key_prefix}_frame_color", disabled=disabled
            )
        with col2:
            frame_text_color = st.color_picker(
                "Color del texto", d.frame_text_color,
                key=f"{key_prefix}_frame_text_color", disabled=disabled,
            )
            frame_scale = st.slider(
                "Grosor del marco", 0.5, 2.0, float(d.frame_scale), step=0.1,
                key=f"{key_prefix}_frame_scale", disabled=disabled,
            )
        frame_font_size = st.slider(
            "Tamaño del texto", 14, 60, int(d.frame_font_size),
            key=f"{key_prefix}_frame_font", disabled=disabled,
        )

    design = DesignSettings(
        pattern=pattern,
        fg_color=fg_color,
        bg_color=bg_color,
        gradient_enabled=gradient_enabled,
        gradient_start=gradient_start,
        gradient_end=gradient_end,
        gradient_direction=gradient_direction,
        box_size=box_size,
        border=border,
        logo_size_ratio=logo_size_ratio,
        transparent_background=transparent,
        frame_style=frame_style,
        frame_text=frame_text,
        frame_color=frame_color,
        frame_text_color=frame_text_color,
        frame_scale=frame_scale,
        frame_font_size=frame_font_size,
    )
    return design, logo_file


def download_row(image: Any, payload: str, name: str, key_prefix: str) -> None:
    """Fila de descargas PNG / JPG / SVG / PDF reutilizando QRExporter."""
    from services.qr_service import export_qr, SIZE_CHOICES
    from utils.helpers import safe_filename

    filename = safe_filename(name, "intelliqr-qr")

    col1, col2 = st.columns([2, 3])
    with col1:
        size_choice = st.selectbox(
            "Tamaño de impresión", SIZE_CHOICES, key=f"{key_prefix}_size"
        )
    custom_w = custom_h = None
    if size_choice == "Personalizado":
        with col2:
            c1, c2 = st.columns(2)
            custom_w = c1.number_input("Ancho (cm)", 1.0, 50.0, 5.0, key=f"{key_prefix}_cw")
            custom_h = c2.number_input("Alto (cm)", 1.0, 50.0, 5.0, key=f"{key_prefix}_ch")

    cols = st.columns(4)
    formats = [("PNG", "image/png"), ("JPG", "image/jpeg"),
               ("SVG", "image/svg+xml"), ("PDF", "application/pdf")]
    for col, (fmt, mime) in zip(cols, formats):
        with col:
            try:
                data = export_qr(
                    image, fmt, payload, filename,
                    size_choice=size_choice, custom_w=custom_w, custom_h=custom_h,
                )
                st.download_button(
                    fmt, data=data, file_name=f"{filename}.{fmt.lower()}",
                    mime=mime, key=f"{key_prefix}_dl_{fmt}", width="stretch",
                )
            except Exception:  # noqa: BLE001
                st.button(fmt, disabled=True, key=f"{key_prefix}_dl_{fmt}_off",
                          width="stretch")

    st.caption(
        "El SVG es el QR base vectorial (sin logo ni degradado), ideal para imprenta. "
        "PNG y PDF incluyen todo el diseño."
    )
