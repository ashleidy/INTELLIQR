
from __future__ import annotations
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Optional

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer,
    RoundedModuleDrawer,
    CircleModuleDrawer,
    GappedSquareModuleDrawer,
    VerticalBarsDrawer,
)
from qrcode.image.styles.colormasks import SolidFillColorMask, HorizontalGradiantColorMask, VerticalGradiantColorMask
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image

_ERROR_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}

_PATTERN_DRAWERS = {
    "cuadrado": SquareModuleDrawer,
    "redondeado": RoundedModuleDrawer,
    "puntos": CircleModuleDrawer,
    "suave": GappedSquareModuleDrawer,
    "moderno": VerticalBarsDrawer,
}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


@dataclass
class QRDesignOptions:
    """Opciones de personalización visual del QR (sección 14-15 del spec)."""
    pattern: str = "cuadrado"          # cuadrado | redondeado | puntos | suave | moderno
    corner_style: str = "cuadradas"    # informativo; los drawers ya cubren la mayoría visualmente
    fg_color: str = "#0F172A"
    bg_color: str = "#FFFFFF"
    gradient_enabled: bool = False
    gradient_start: str = "#2563EB"
    gradient_end: str = "#60A5FA"
    gradient_direction: str = "horizontal"  # horizontal | vertical
    logo_path: Optional[str] = None
    # NUEVO (migración web): en Streamlit Cloud el sistema de archivos es
    # efímero y el logo llega como un objeto en memoria (UploadedFile /
    # BytesIO / bytes). `logo_path` se conserva intacto para la app de
    # escritorio y para los tests existentes; si ambos vienen, gana este.
    logo_bytes: Optional[object] = None
    logo_size_ratio: float = 0.22       # % del ancho del QR que debe ocupar el logo
    box_size: int = 10
    border: int = 4                     # zona de silencio mínima (nunca 0)
    transparent_background: bool = False  # hace transparente el color de fondo (solo PNG/SVG)


@dataclass
class QRGenerationResult:
    image: Image.Image
    error_correction_used: str
    warnings: list[str] = field(default_factory=list)


class QRGenerator:
    """Motor central: payload -> QR Matrix -> Customization -> imagen PIL."""

    MIN_BORDER = 2  # nunca permitir eliminar completamente la zona de silencio

    def generate(self, payload: str, design: Optional[QRDesignOptions] = None) -> QRGenerationResult:
        design = design or QRDesignOptions()
        warnings: list[str] = []

        border = max(design.border, self.MIN_BORDER)

        has_logo = bool(design.logo_path or design.logo_bytes)
        error_correction = "H" if has_logo else "M"
        if has_logo and design.logo_size_ratio > 0.3:
            warnings.append("El logo es demasiado grande y puede afectar la lectura del código.")

        qr = qrcode.QRCode(
            error_correction=_ERROR_LEVELS[error_correction],
            box_size=design.box_size,
            border=border,
        )
        qr.add_data(payload)
        qr.make(fit=True)

        drawer_cls = _PATTERN_DRAWERS.get(design.pattern, SquareModuleDrawer)
        module_drawer = drawer_cls()

        fg = _hex_to_rgb(design.fg_color)
        bg = _hex_to_rgb(design.bg_color)

        if design.gradient_enabled:
            start = _hex_to_rgb(design.gradient_start)
            end = _hex_to_rgb(design.gradient_end)
            mask_cls = VerticalGradiantColorMask if design.gradient_direction == "vertical" else HorizontalGradiantColorMask
            color_mask = mask_cls(back_color=bg, left_color=start, right_color=end) \
                if mask_cls is HorizontalGradiantColorMask else mask_cls(back_color=bg, top_color=start, bottom_color=end)
        else:
            color_mask = SolidFillColorMask(front_color=fg, back_color=bg)

        # IMPORTANTE: NO le pasamos el logo a qrcode/StyledPilImage aquí.
        # Su propio mecanismo de "embeded_image_path" usa un tamaño fijo
        # interno que ignora por completo nuestro control deslizante de
        # tamaño — ese era el bug ("no hay aumento de imagen al agregar
        # logo"). En su lugar generamos el QR limpio y pegamos el logo
        # nosotros mismos más abajo, con el tamaño exacto que pida el usuario.
        image = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            color_mask=color_mask,
        )
        pil_image = image.get_image() if hasattr(image, "get_image") else image
        pil_image = pil_image.convert("RGB")

        if has_logo:
            pil_image = self._embed_logo(
                pil_image,
                design.logo_path,
                design.logo_size_ratio,
                logo_bytes=design.logo_bytes,
            )

        if design.transparent_background and not design.gradient_enabled:
            pil_image = self._make_bg_transparent(pil_image, bg)

        return QRGenerationResult(image=pil_image, error_correction_used=error_correction, warnings=warnings)

    @staticmethod
    def _embed_logo(qr_image: Image.Image, logo_path: str | None, ratio: float,
                    logo_bytes: object | None = None) -> Image.Image:
        """Pega el logo centrado sobre el QR, con el tamaño (%) que el usuario
        eligió en el control deslizante — esto es lo que antes no funcionaba.

        Acepta una ruta en disco (escritorio) o un objeto en memoria
        (bytes / BytesIO / UploadedFile de Streamlit)."""
        try:
            if logo_bytes is not None:
                raw = logo_bytes.getvalue() if hasattr(logo_bytes, "getvalue") else (
                    logo_bytes.read() if hasattr(logo_bytes, "read") else logo_bytes
                )
                logo = Image.open(BytesIO(raw)).convert("RGBA")
            else:
                if not logo_path or not Path(logo_path).exists():
                    return qr_image
                logo = Image.open(logo_path).convert("RGBA")
        except Exception:
            return qr_image

        qr_w, qr_h = qr_image.size
        ratio = max(0.05, min(ratio, 0.5))  # límites de seguridad
        target_size = max(int(min(qr_w, qr_h) * ratio), 16)

        # Redimensiona el logo manteniendo proporción dentro de target_size x target_size.
        logo_copy = logo.copy()
        logo_copy.thumbnail((target_size, target_size), Image.LANCZOS)

        # Fondo blanco detrás del logo para no perder legibilidad del QR bajo él.
        pad = max(int(max(logo_copy.size) * 0.14), 4)
        backing_w = logo_copy.width + pad * 2
        backing_h = logo_copy.height + pad * 2
        backing = Image.new("RGBA", (backing_w, backing_h), (255, 255, 255, 255))
        backing.paste(logo_copy, (pad, pad), logo_copy)

        base = qr_image.convert("RGBA")
        position = ((qr_w - backing_w) // 2, (qr_h - backing_h) // 2)
        base.alpha_composite(backing, position)
        return base.convert("RGB")

    @staticmethod
    def _make_bg_transparent(image: Image.Image, bg_rgb: tuple[int, int, int]) -> Image.Image:
        """Convierte a RGBA y pone alfa 0 en los píxeles que coinciden con el color de fondo."""
        rgba = image.convert("RGBA")
        pixels = rgba.getdata()
        new_pixels = [
            (r, g, b, 0) if (r, g, b) == bg_rgb else (r, g, b, a)
            for (r, g, b, a) in pixels
        ]
        rgba.putdata(new_pixels)
        return rgba

    @staticmethod
    def to_bytes(image: Image.Image, fmt: str = "PNG") -> bytes:
        buf = BytesIO()
        image.save(buf, format=fmt)
        return buf.getvalue()
