
from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal
import re

from PIL import Image
import qrcode
from qrcode.image.svg import SvgPathImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdf_canvas

ExportFormat = Literal["PNG", "JPG", "SVG", "PDF"]

_SIZE_PRESETS_CM = {
    "Pequeño": (3, 3),
    "Mediano": (5, 5),
    "Grande": (10, 10),
}


@dataclass
class ExportOptions:
    fmt: ExportFormat = "PNG"
    dpi: int = 300
    size_cm: tuple[float, float] | None = None
    margin_cm: float = 0.0
    orientation: str = "vertical"
    name: str | None = None


def _sanitize_filename(name: str) -> str:
    """Quita caracteres inválidos en Windows/macOS/Linux y espacios sobrantes."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip().strip(".")
    return name or "qr"


class QRExporter:
    def export(self, image: Image.Image, output_path: str | Path,
               options: ExportOptions, payload: str | None = None) -> Path:
        output_path = Path(output_path)

        if options.name:
            safe = _sanitize_filename(options.name)
            output_path = output_path.with_name(f"{safe}{output_path.suffix}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if options.fmt in ("PNG", "JPG"):
            self._export_raster(image, output_path, options)
        elif options.fmt == "SVG":
            self._export_svg(payload or "", output_path)
        elif options.fmt == "PDF":
            self._export_pdf(image, output_path, options)
        else:
            raise ValueError(f"Formato de exportación no soportado: {options.fmt}")
        return output_path

    # ---- NUEVO (migración web) -------------------------------------------
    # Streamlit no descarga desde una ruta en disco: necesita los bytes del
    # archivo. Reutiliza exactamente la misma lógica de export() escribiendo
    # en un archivo temporal, para no duplicar el código de PNG/JPG/SVG/PDF
    # ni arriesgarse a que las dos rutas diverjan con el tiempo.
    def export_bytes(self, image: Image.Image, options: ExportOptions,
                     payload: str | None = None) -> bytes:
        import tempfile

        suffix = {"PNG": ".png", "JPG": ".jpg", "SVG": ".svg", "PDF": ".pdf"}.get(options.fmt)
        if suffix is None:
            raise ValueError(f"Formato de exportación no soportado: {options.fmt}")

        opts = ExportOptions(
            fmt=options.fmt, dpi=options.dpi, size_cm=options.size_cm,
            margin_cm=options.margin_cm, orientation=options.orientation, name=None,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / f"intelliqr{suffix}"
            self.export(image, target, opts, payload=payload)
            return target.read_bytes()

    def _export_raster(self, image: Image.Image, output_path: Path, options: ExportOptions) -> None:
        img = image
        if options.size_cm:
            width_px = int(options.size_cm[0] / 2.54 * options.dpi)
            height_px = int(options.size_cm[1] / 2.54 * options.dpi)
            img = image.resize((width_px, height_px), Image.LANCZOS)
        save_kwargs = {"dpi": (options.dpi, options.dpi)}
        if options.fmt == "JPG":
            img = img.convert("RGB")
            img.save(output_path, format="JPEG", quality=95, **save_kwargs)
        else:
            img.save(output_path, format="PNG", **save_kwargs)

    def _export_svg(self, payload: str, output_path: Path) -> None:
        factory = SvgPathImage
        img = qrcode.make(payload, image_factory=factory)
        img.save(str(output_path))

    def _export_pdf(self, image: Image.Image, output_path: Path, options: ExportOptions) -> None:
        page_size = A4
        c = pdf_canvas.Canvas(str(output_path), pagesize=page_size)
        page_w, page_h = page_size

        if options.size_cm:
            qr_w, qr_h = options.size_cm[0] * cm, options.size_cm[1] * cm
        else:
            qr_w, qr_h = 8 * cm, 8 * cm

        margin = options.margin_cm * cm
        x = (page_w - qr_w) / 2
        y = (page_h - qr_h) / 2

        tmp_png = output_path.with_suffix(".tmp.png")
        image.save(tmp_png, format="PNG", dpi=(options.dpi, options.dpi))
        c.drawImage(str(tmp_png), x, y, width=qr_w, height=qr_h)
        c.showPage()
        c.save()
        tmp_png.unlink(missing_ok=True)


def resolve_size_cm(size_choice: str, custom_w: float | None = None,
                    custom_h: float | None = None) -> tuple[float, float] | None:
    if size_choice == "Personalizado" and custom_w and custom_h:
        return (custom_w, custom_h)
    return _SIZE_PRESETS_CM.get(size_choice)


def image_to_bytes(image: Image.Image, fmt: str = "PNG", dpi: int = 300) -> bytes:
    """Atajo para vistas previas y descargas rápidas sin pasar por disco."""
    buf = BytesIO()
    if fmt.upper() in ("JPG", "JPEG"):
        image.convert("RGB").save(buf, format="JPEG", quality=95, dpi=(dpi, dpi))
    else:
        image.save(buf, format="PNG", dpi=(dpi, dpi))
    return buf.getvalue()
