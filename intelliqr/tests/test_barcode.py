"""
Tests del motor de códigos de barras (BWIPP), cubriendo todas las
categorías de tec-it.com que soportamos (sección 22, 48.15).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from core.barcode_engine.generator import BarcodeGenerator, TYPES, CATEGORIES, TWO_D_TYPES
from core.barcode_engine.validator import validate_barcode


def test_categories_cover_expected_groups():
    expected = {
        "Códigos lineales", "EAN / UPC", "GS1 DataBar", "Códigos ISBN",
        "Códigos de sanidad", "Códigos 2D", "Códigos GS1 2D", "Códigos postales",
    }
    assert expected.issubset(set(CATEGORIES.keys()))


def test_every_type_has_a_working_example():
    """El ejemplo mostrado al usuario en la UI debe generarse sin error,
    para cada uno de los ~39 tipos del catálogo."""
    gen = BarcodeGenerator()
    failures = []
    for type_id, info in TYPES.items():
        try:
            result = gen.generate(type_id, info.placeholder, show_text=True)
            assert result.image.size[0] > 0
        except Exception as exc:
            failures.append((type_id, str(exc)))
    assert not failures, f"Tipos cuyo propio ejemplo falla: {failures}"


def test_validate_empty_value_rejected():
    result = validate_barcode("code128", "   ")
    assert not result.is_valid


def test_validate_nonempty_value_accepted():
    result = validate_barcode("code128", "ABC123")
    assert result.is_valid


def test_ean13_auto_check_digit():
    """BWIPP calcula el dígito de control si se dan 12 dígitos."""
    gen = BarcodeGenerator()
    result = gen.generate("ean13", "400638133393")
    assert result.image.size[0] > 0


def test_unknown_type_raises_friendly_error():
    gen = BarcodeGenerator()
    with pytest.raises(ValueError):
        gen.generate("tipo_inexistente", "123")


def test_2d_types_flagged_correctly():
    assert "datamatrix" in TWO_D_TYPES
    assert "pdf417" in TWO_D_TYPES
    assert "code128" not in TWO_D_TYPES


def test_gs1_databar_generates():
    gen = BarcodeGenerator()
    result = gen.generate("databaromni", "(01)09521234543213")
    assert result.image.size[0] > 0


def test_postal_royalmail_generates():
    gen = BarcodeGenerator()
    result = gen.generate("royalmail", "AB1234567890")
    assert result.image.size[0] > 0


def test_isbn_generates():
    gen = BarcodeGenerator()
    result = gen.generate("isbn", "978-0-306-40615-7")
    assert result.image.size[0] > 0
