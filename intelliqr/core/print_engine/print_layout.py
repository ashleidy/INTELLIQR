
from __future__ import annotations
from dataclasses import dataclass

CM_TO_MM = 10

PAGE_SIZES_MM = {
    "A4": (210.0, 297.0),
    "Carta": (215.9, 279.4),
}


@dataclass
class PrintLayoutOptions:
    page_size: str = "A4"                 # A4 | Carta | Personalizado
    custom_page_w_mm: float = 210.0
    custom_page_h_mm: float = 297.0
    orientation: str = "vertical"           # vertical | horizontal
    margin_mm: float = 10.0
    item_size_mm: float = 50.0               # tamaño de cada copia (cuadrada)
    spacing_mm: float = 4.0                   # separación entre copias
    copies: int = 1


@dataclass
class PrintLayoutResult:
    page_w_mm: float
    page_h_mm: float
    columns: int
    rows: int
    per_page: int
    pages_needed: int
    positions_per_page: list[tuple[float, float]]  # esquina superior-izquierda (mm) de cada copia


def compute_layout(options: PrintLayoutOptions) -> PrintLayoutResult:
    if options.page_size == "Personalizado":
        page_w, page_h = options.custom_page_w_mm, options.custom_page_h_mm
    else:
        page_w, page_h = PAGE_SIZES_MM.get(options.page_size, PAGE_SIZES_MM["A4"])

    if options.orientation == "horizontal" and page_w < page_h:
        page_w, page_h = page_h, page_w

    usable_w = max(page_w - options.margin_mm * 2, 1)
    usable_h = max(page_h - options.margin_mm * 2, 1)

    step = options.item_size_mm + options.spacing_mm
    columns = max(int((usable_w + options.spacing_mm) // step), 1)
    rows = max(int((usable_h + options.spacing_mm) // step), 1)
    per_page = columns * rows

    positions: list[tuple[float, float]] = []
    for row in range(rows):
        for col in range(columns):
            x = options.margin_mm + col * step
            y = options.margin_mm + row * step
            positions.append((x, y))

    pages_needed = max(1, -(-options.copies // per_page))  # redondeo hacia arriba

    return PrintLayoutResult(
        page_w_mm=page_w, page_h_mm=page_h,
        columns=columns, rows=rows, per_page=per_page,
        pages_needed=pages_needed, positions_per_page=positions,
    )
