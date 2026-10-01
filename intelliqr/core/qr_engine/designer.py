from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


@dataclass
class FrameOptions:
    # ninguno | simple | redondeado | moderno | etiqueta | promocional |
    # circular | telefono | navegador | bolsa
    style: str = "ninguno"
    text: str = "ESCANÉAME"
    text_color: str = "#FFFFFF"
    frame_color: str = "#2563EB"
    font_size: int = 28
    padding: int = 24
    # NUEVO: multiplicador global del grosor/márgenes del marco.
    # 0.5 = marco fino, 1.0 = normal, 2.0 = marco grueso.
    frame_scale: float = 1.0


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


def _load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _s(value: float, scale: float, minimum: int = 1) -> int:
    """Escala una dimensión estructural del marco (padding, borde, radio…).
    Nunca devuelve menos que `minimum` para evitar marcos degenerados."""
    scale = max(scale, 0.1)
    return max(int(round(value * scale)), minimum)


def _draw_centered_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str,
                         color: tuple[int, int, int], font: ImageFont.ImageFont) -> None:
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x0 + (x1 - x0 - text_w) / 2, y0 + (y1 - y0 - text_h) / 2),
              text, fill=color, font=font)


def _draw_caption_band(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str,
                        frame_color: tuple[int, int, int], text_color: tuple[int, int, int],
                        font: ImageFont.ImageFont, radius: int = 0) -> None:
    """Franja rellena de frame_color con el texto centrado en text_color.
    Garantiza contraste sin importar qué colores elija el usuario."""
    if radius:
        draw.rounded_rectangle(box, radius=radius, fill=frame_color)
    else:
        draw.rectangle(box, fill=frame_color)
    _draw_centered_text(draw, box, text.upper(), text_color, font)


def _band_frame(qr_image: Image.Image, options: FrameOptions, band_on_top: bool = False) -> Image.Image:
    scale = options.frame_scale
    qr_w, qr_h = qr_image.size
    pad = _s(options.padding, scale)
    band_height = options.font_size + pad
    frame_color = _hex_to_rgb(options.frame_color)
    text_color = _hex_to_rgb(options.text_color)

    total_w = qr_w + pad * 2
    total_h = qr_h + pad * 2 + band_height

    canvas = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(canvas)

    if band_on_top:
        canvas.paste(qr_image, (pad, band_height + pad // 2))
        _draw_caption_band(draw, (0, 0, total_w, band_height),
                           options.text, frame_color, text_color, _load_font(options.font_size))
    else:
        canvas.paste(qr_image, (pad, (total_h - band_height - qr_h) // 2))
        _draw_caption_band(draw, (0, total_h - band_height, total_w, total_h),
                           options.text, frame_color, text_color, _load_font(options.font_size))
    return canvas


def _rounded_frame(qr_image: Image.Image, options: FrameOptions) -> Image.Image:
    scale = options.frame_scale
    qr_w, qr_h = qr_image.size
    pad = _s(options.padding, scale)
    band_height = options.font_size + pad
    radius = _s(18, scale, 6)
    border_w = _s(4, scale, 2)
    frame_color = _hex_to_rgb(options.frame_color)
    text_color = _hex_to_rgb(options.text_color)

    total_w = qr_w + pad * 2
    total_h = qr_h + pad * 2 + band_height

    canvas = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([2, 2, total_w - 2, total_h - 2],
                           radius=radius, outline=frame_color, width=border_w)
    canvas.paste(qr_image, (pad, pad))
    _draw_caption_band(
        draw, (2, total_h - band_height, total_w - 2, total_h - 2),
        options.text, frame_color, text_color, _load_font(options.font_size),
        radius=max(radius - 2, 4),
    )
    return canvas


def _promo_frame(qr_image: Image.Image, options: FrameOptions) -> Image.Image:
    scale = options.frame_scale
    qr_w, qr_h = qr_image.size
    pad = _s(options.padding, scale)
    frame_color = _hex_to_rgb(options.frame_color)
    text_color = _hex_to_rgb(options.text_color)

    total_w = qr_w + pad * 2
    total_h = qr_h + pad * 2

    canvas = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(canvas)

    dash_len = _s(10, scale)
    gap_len = _s(6, scale)
    border_w = _s(3, scale, 2)
    for x in range(0, total_w, dash_len + gap_len):
        draw.line([(x, 0), (min(x + dash_len, total_w), 0)], fill=frame_color, width=border_w)
        draw.line([(x, total_h - border_w), (min(x + dash_len, total_w), total_h - border_w)],
                  fill=frame_color, width=border_w)
    for y in range(0, total_h, dash_len + gap_len):
        draw.line([(0, y), (0, min(y + dash_len, total_h))], fill=frame_color, width=border_w)
        draw.line([(total_w - border_w, y), (total_w - border_w, min(y + dash_len, total_h))],
                  fill=frame_color, width=border_w)

    canvas.paste(qr_image, (pad, pad))

    font = _load_font(max(options.font_size - 6, 12))
    text = options.text.upper()
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    badge_pad_x = _s(14, scale)
    badge_pad_y = _s(8, scale)
    badge_w = min(text_w + badge_pad_x * 2, total_w - _s(16, scale))
    badge_h = text_h + badge_pad_y * 2
    badge_x1 = total_w - _s(10, scale)
    badge_x0 = badge_x1 - badge_w
    badge_y0 = _s(10, scale)
    badge_y1 = badge_y0 + badge_h

    draw.rounded_rectangle([badge_x0, badge_y0, badge_x1, badge_y1],
                           radius=badge_h // 2, fill=frame_color)
    _draw_centered_text(draw, (badge_x0, badge_y0, badge_x1, badge_y1),
                        text, text_color, font)
    return canvas


def _sticker_frame(qr_image: Image.Image, options: FrameOptions) -> Image.Image:
    scale = options.frame_scale
    qr_w, qr_h = qr_image.size
    pad = _s(options.padding, scale)
    frame_color = _hex_to_rgb(options.frame_color)
    text_color = _hex_to_rgb(options.text_color)
    band_height = options.font_size + _s(16, scale)

    total_w = qr_w + pad * 2
    total_h = qr_h + pad * 2 + band_height

    canvas = Image.new("RGB", (total_w, total_h), frame_color)
    draw = ImageDraw.Draw(canvas)
    canvas.paste(qr_image, (pad, pad))
    _draw_caption_band(draw, (0, total_h - band_height, total_w, total_h),
                       options.text, frame_color, text_color, _load_font(options.font_size))
    return canvas


def _circular_frame(qr_image: Image.Image, options: FrameOptions) -> Image.Image:
    scale = options.frame_scale
    qr_w, qr_h = qr_image.size
    frame_color = _hex_to_rgb(options.frame_color)
    text_color = _hex_to_rgb(options.text_color)
    diameter = int(max(qr_w, qr_h) * (1.0 + 0.35 * max(scale, 0.1)))
    ring_thickness = _s(10, scale, 2)
    band_height = options.font_size + _s(20, scale)
    band_margin = _s(20, scale)

    total_w = diameter + _s(20, scale)
    total_h = diameter + _s(20, scale) + band_height + _s(10, scale)

    canvas = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(canvas)
    top_offset = _s(10, scale)
    cx, cy = total_w // 2, top_offset + diameter // 2
    draw.ellipse([cx - diameter // 2, cy - diameter // 2, cx + diameter // 2, cy + diameter // 2],
                 outline=frame_color, width=ring_thickness)
    canvas.paste(qr_image, (cx - qr_w // 2, cy - qr_h // 2))
    band_top = total_h - band_height - _s(6, scale)
    _draw_caption_band(
        draw, (band_margin, band_top, total_w - band_margin, band_top + band_height),
        options.text, frame_color, text_color, _load_font(options.font_size),
        radius=band_height // 2,
    )
    return canvas


def _phone_frame(qr_image: Image.Image, options: FrameOptions) -> Image.Image:
    scale = options.frame_scale
    qr_w, qr_h = qr_image.size
    frame_color = _hex_to_rgb(options.frame_color)
    text_color = _hex_to_rgb(options.text_color)
    side_margin = _s(22, scale)
    top_margin = _s(34, scale)
    band_height = options.font_size + _s(20, scale)
    bottom_margin = band_height + _s(14, scale)
    border_w = _s(6, scale, 2)
    corner_r = _s(28, scale, 8)
    outer_pad = _s(6, scale, 2)

    body_w = qr_w + side_margin * 2
    body_h = qr_h + top_margin + bottom_margin

    canvas = Image.new("RGB", (body_w + outer_pad * 2, body_h + outer_pad * 2), "white")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([outer_pad, outer_pad, body_w + outer_pad, body_h + outer_pad],
                           radius=corner_r, outline=frame_color, width=border_w)
    speaker_w = body_w // 4
    speaker_h = _s(6, scale, 2)
    speaker_y0 = outer_pad + _s(10, scale)
    draw.rounded_rectangle(
        [outer_pad + (body_w - speaker_w) // 2, speaker_y0,
         outer_pad + (body_w + speaker_w) // 2, speaker_y0 + speaker_h],
        radius=speaker_h // 2, fill=frame_color,
    )
    canvas.paste(qr_image, (outer_pad + side_margin, outer_pad + top_margin))
    band_top = outer_pad + top_margin + qr_h + _s(10, scale)
    _draw_caption_band(
        draw,
        (outer_pad + side_margin // 2, band_top,
         body_w + outer_pad - side_margin // 2, band_top + band_height),
        options.text, frame_color, text_color, _load_font(options.font_size),
        radius=band_height // 2,
    )
    return canvas


def _browser_frame(qr_image: Image.Image, options: FrameOptions) -> Image.Image:
    scale = options.frame_scale
    qr_w, qr_h = qr_image.size
    frame_color = _hex_to_rgb(options.frame_color)
    text_color = _hex_to_rgb(options.text_color)
    pad = _s(16, scale)
    bar_height = _s(30, scale)
    band_height = options.font_size + _s(16, scale)
    border_w = _s(3, scale, 2)
    dot_r = _s(4, scale, 2)
    dot_gap = _s(16, scale)
    dot_start = _s(14, scale)

    total_w = qr_w + pad * 2
    total_h = bar_height + qr_h + pad * 2 + band_height

    canvas = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, total_w, total_h - 1], outline=frame_color, width=border_w)
    draw.rectangle([0, 0, total_w, bar_height], fill=frame_color)
    for i in range(3):
        cx = dot_start + i * dot_gap
        draw.ellipse([cx, bar_height // 2 - dot_r, cx + dot_r * 2, bar_height // 2 + dot_r],
                     fill=(255, 255, 255))
    canvas.paste(qr_image, (pad, bar_height + pad))
    _draw_caption_band(draw, (0, total_h - band_height, total_w, total_h),
                       options.text, frame_color, text_color, _load_font(options.font_size))
    return canvas


def _bag_frame(qr_image: Image.Image, options: FrameOptions) -> Image.Image:
    scale = options.frame_scale
    qr_w, qr_h = qr_image.size
    frame_color = _hex_to_rgb(options.frame_color)
    text_color = _hex_to_rgb(options.text_color)
    pad = _s(26, scale)
    handle_h = _s(26, scale)
    band_height = options.font_size + _s(16, scale)
    border_w = _s(5, scale, 2)
    outer_pad = _s(6, scale, 2)

    top_w = qr_w + pad
    bottom_w = qr_w + pad * 2
    body_h = qr_h + pad * 2

    total_w = bottom_w + outer_pad * 2
    total_h = handle_h + body_h + band_height + outer_pad * 2

    canvas = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(canvas)

    cx = total_w // 2
    top_y = handle_h + outer_pad
    bottom_y = top_y + body_h
    trapezoid = [
        (cx - top_w // 2, top_y), (cx + top_w // 2, top_y),
        (cx + bottom_w // 2, bottom_y), (cx - bottom_w // 2, bottom_y),
    ]
    draw.polygon(trapezoid, outline=frame_color, width=border_w)
    handle_span = top_w // 3
    draw.arc([cx - handle_span, outer_pad, cx - handle_span // 3, top_y + _s(14, scale)],
             start=180, end=360, fill=frame_color, width=border_w)
    draw.arc([cx + handle_span // 3, outer_pad, cx + handle_span, top_y + _s(14, scale)],
             start=180, end=360, fill=frame_color, width=border_w)

    canvas.paste(qr_image, (cx - qr_w // 2, top_y + pad // 2))
    _draw_caption_band(draw, (0, total_h - band_height, total_w, total_h),
                       options.text, frame_color, text_color, _load_font(options.font_size))
    return canvas


_BUILDERS = {
    "simple": lambda img, opt: _band_frame(img, opt, band_on_top=False),
    "moderno": lambda img, opt: _band_frame(img, opt, band_on_top=True),
    "redondeado": _rounded_frame,
    "etiqueta": _sticker_frame,
    "promocional": _promo_frame,
    "circular": _circular_frame,
    "telefono": _phone_frame,
    "navegador": _browser_frame,
    "bolsa": _bag_frame,
}


def apply_frame(qr_image: Image.Image, options: Optional[FrameOptions]) -> Image.Image:
    if options is None or options.style == "ninguno":
        return qr_image
    builder = _BUILDERS.get(options.style)
    if builder is None:
        return qr_image
    # blindaje: nunca dejar el marco con escala inválida
    if options.frame_scale <= 0:
        options.frame_scale = 1.0
    return builder(qr_image, options)