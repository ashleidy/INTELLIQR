"""Tests de contraste de texto en los marcos (regresión del bug de texto invisible)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from core.qr_engine.generator import QRGenerator, QRDesignOptions
from core.qr_engine.designer import FrameOptions, apply_frame

_STYLES = ["simple", "moderno", "redondeado", "etiqueta", "promocional",
           "circular", "telefono", "navegador", "bolsa"]


def _has_text_color_pixels(image, rgb, min_count=20):
    arr = np.array(image.convert("RGB"))
    mask = (arr[:, :, 0] == rgb[0]) & (arr[:, :, 1] == rgb[1]) & (arr[:, :, 2] == rgb[2])
    return mask.sum() >= min_count


def test_all_frames_render_visible_text_with_default_white_text_color():
    """Caso exacto que fallaba: texto blanco (valor por defecto) debe seguir
    siendo visible en TODAS las formas, no solo en las que ya tenían banda."""
    gen = QRGenerator()
    base = gen.generate("https://intelliqr.app", QRDesignOptions(box_size=6, border=1))

    for style in _STYLES:
        opts = FrameOptions(style=style, text="SCAN ME", frame_color="#2563EB", text_color="#FFFFFF")
        img = apply_frame(base.image, opts)
        assert _has_text_color_pixels(img, (255, 255, 255)), f"'{style}' no muestra texto blanco visible"


def test_all_frames_render_visible_text_with_dark_text_color():
    """Mismo caso con texto oscuro sobre marco claro, para cubrir la combinación inversa."""
    gen = QRGenerator()
    base = gen.generate("https://intelliqr.app", QRDesignOptions(box_size=6, border=1))

    for style in _STYLES:
        opts = FrameOptions(style=style, text="SCAN ME", frame_color="#F59E0B", text_color="#0F172A")
        img = apply_frame(base.image, opts)
        assert _has_text_color_pixels(img, (15, 23, 42)), f"'{style}' no muestra texto oscuro visible"


def test_no_frame_style_untouched():
    gen = QRGenerator()
    base = gen.generate("https://intelliqr.app", QRDesignOptions())
    result = apply_frame(base.image, FrameOptions(style="ninguno"))
    assert result.size == base.image.size


def test_promocional_and_etiqueta_are_visually_different():
    """Regresión: 'promocional' estaba mapeado a la misma función que
    'etiqueta' y producía una imagen idéntica."""
    import hashlib
    gen = QRGenerator()
    base = gen.generate("https://intelliqr.app", QRDesignOptions(box_size=6, border=1))
    img_etiqueta = apply_frame(base.image, FrameOptions(style="etiqueta", text="OFERTA", frame_color="#DC2626"))
    img_promo = apply_frame(base.image, FrameOptions(style="promocional", text="OFERTA", frame_color="#DC2626"))
    h1 = hashlib.md5(img_etiqueta.tobytes()).hexdigest()
    h2 = hashlib.md5(img_promo.tobytes()).hexdigest()
    assert h1 != h2


def test_promocional_handles_long_text_without_crashing():
    gen = QRGenerator()
    base = gen.generate("https://intelliqr.app", QRDesignOptions(box_size=6, border=1))
    img = apply_frame(base.image, FrameOptions(style="promocional", text="NUEVO PRODUCTO ESPECIAL DE TEMPORADA"))
    assert img.size[0] > 0
