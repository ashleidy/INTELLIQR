"""Tests del motor de escaneo (sección 26, 48.15): round-trip con QR y barras."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.qr_engine.generator import QRGenerator, QRDesignOptions
from core.barcode_engine.generator import BarcodeGenerator
from core.scan_engine.scanner import Scanner, classify_action


def test_scan_roundtrip_qr_url():
    gen = QRGenerator()
    result = gen.generate("https://intelliqr.app", QRDesignOptions())
    scans = Scanner().decode(result.image)
    assert len(scans) == 1
    assert scans[0].type_label == "Código QR"
    assert scans[0].content == "https://intelliqr.app"


def test_scan_roundtrip_qr_whatsapp():
    gen = QRGenerator()
    payload = "https://wa.me/573001234567?text=Hola"
    result = gen.generate(payload, QRDesignOptions())
    scans = Scanner().decode(result.image)
    assert scans[0].content == payload


def test_scan_roundtrip_barcode_ean13():
    gen = BarcodeGenerator()
    result = gen.generate("ean13", "4006381333931")
    scans = Scanner().decode(result.image)
    assert len(scans) == 1
    assert scans[0].type_label == "EAN-13"
    assert scans[0].content == "4006381333931"


def test_scan_roundtrip_barcode_code128():
    gen = BarcodeGenerator()
    result = gen.generate("code128", "PRODUCTO-001")
    scans = Scanner().decode(result.image)
    assert scans[0].content == "PRODUCTO-001"


def test_scan_no_code_found():
    from PIL import Image
    blank = Image.new("RGB", (100, 100), "white")
    scans = Scanner().decode(blank)
    assert scans == []


def test_classify_action_url():
    assert classify_action("https://intelliqr.app") == "https://intelliqr.app"


def test_classify_action_plain_text_not_openable():
    assert classify_action("solo un texto cualquiera") is None
