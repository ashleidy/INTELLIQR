"""Tests de idioma, tamaño de letra y el motor de impresión."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.i18n import tr, set_language, get_language
from ui import theme
from core.print_engine.print_layout import compute_layout, PrintLayoutOptions


def test_translation_switches_language():
    set_language("es")
    assert tr("home.title") == "Bienvenido a IntelliQR"
    set_language("en")
    assert tr("home.title") == "Welcome to IntelliQR"
    set_language("es")  # dejar el estado global limpio para otros tests


def test_translation_unknown_key_falls_back_gracefully():
    assert tr("clave.que.no.existe") == "clave.que.no.existe"


def test_font_scale_changes_stylesheet_sizes():
    normal = theme.build_stylesheet(1.0)
    large = theme.build_stylesheet(1.3)
    # El tamaño de H1 se toma del propio tema, para que el test no se rompa
    # cada vez que se ajusta la escala tipográfica.
    assert f"{round(theme._BASE_H1 * 1.0)}px" in normal
    assert f"{round(theme._BASE_H1 * 1.3)}px" in large
    assert normal != large


def test_print_layout_basic_grid():
    opts = PrintLayoutOptions(page_size="A4", margin_mm=10, item_size_mm=50, spacing_mm=4, copies=1)
    result = compute_layout(opts)
    assert result.columns >= 1 and result.rows >= 1
    assert result.pages_needed == 1


def test_print_layout_multiple_pages():
    opts = PrintLayoutOptions(page_size="A4", margin_mm=10, item_size_mm=50, spacing_mm=4, copies=100)
    result = compute_layout(opts)
    assert result.pages_needed > 1
    assert result.pages_needed == -(-100 // result.per_page)


def test_print_layout_custom_page_size():
    opts = PrintLayoutOptions(page_size="Personalizado", custom_page_w_mm=100, custom_page_h_mm=150,
                               margin_mm=5, item_size_mm=30, copies=1)
    result = compute_layout(opts)
    assert result.page_w_mm == 100
    assert result.page_h_mm == 150


def test_print_layout_horizontal_orientation_swaps_dimensions():
    opts = PrintLayoutOptions(page_size="A4", orientation="horizontal", copies=1)
    result = compute_layout(opts)
    assert result.page_w_mm > result.page_h_mm


def test_qr_design_is_actually_persisted():
    """Regresión: el diseño (patrón, colores, marco) se perdía al guardar
    porque el QRDesign nuevo nunca se añadía a la sesión."""
    from database.database import init_db
    from database.repositories.qr_repository import QRRepository

    init_db()
    repo = QRRepository()
    qr_id = repo.save(
        name="test_design_persist",
        type_id="url",
        payload="https://ejemplo.test",
        content_data={"url": "https://ejemplo.test"},
        design_data={"pattern": "puntos", "fg_color": "#FF0000", "frame_style": "moderno"},
    )
    record = repo.get(qr_id)
    assert record is not None and record.design is not None
    assert record.design.pattern == "puntos"
    assert record.design.fg_color == "#FF0000"
    assert record.design.frame_style == "moderno"
    repo.delete(qr_id)
