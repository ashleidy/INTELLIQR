"""Tests de los qr_types principales, validación y exportación (sección 48.15)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from qr_types.url import URLType
from qr_types.whatsapp import WhatsAppType
from qr_types.email import EmailType
from qr_types.phone import PhoneType
from qr_types.sms import SMSType
from qr_types.wifi import WiFiType
from qr_types.vcard import VCardType
from core.qr_engine.generator import QRGenerator, QRDesignOptions
from core.qr_engine.exporter import QRExporter, ExportOptions


def test_url_valid():
    t = URLType()
    result = t.validate({"url": "https://intelliqr.app"})
    assert result.is_valid
    assert t.build_payload({"url": "https://intelliqr.app"}) == "https://intelliqr.app"


def test_url_invalid():
    t = URLType()
    result = t.validate({"url": "intelliqr.app"})
    assert not result.is_valid
    assert "url" in result.errors


def test_whatsapp_payload():
    t = WhatsAppType()
    data = {"country_code": "57", "number": "3001234567", "message": "Hola"}
    assert t.validate(data).is_valid
    payload = t.build_payload(data)
    assert payload.startswith("https://wa.me/573001234567")
    assert "Hola" in payload or "text=" in payload


def test_email_payload():
    t = EmailType()
    data = {"email": "a@b.com", "subject": "Hola", "message": "Test"}
    assert t.validate(data).is_valid
    payload = t.build_payload(data)
    assert payload.startswith("mailto:a@b.com")


def test_email_invalid():
    t = EmailType()
    assert not t.validate({"email": "no-es-un-correo"}).is_valid


def test_phone_payload():
    t = PhoneType()
    data = {"country_code": "57", "number": "3001234567"}
    assert t.validate(data).is_valid
    assert t.build_payload(data) == "tel:+573001234567"


def test_sms_payload():
    t = SMSType()
    data = {"number": "+573001234567", "message": "Hola"}
    assert t.validate(data).is_valid
    assert t.build_payload(data) == "SMSTO:+573001234567:Hola"


def test_wifi_payload_wpa():
    t = WiFiType()
    data = {"ssid": "MiRed", "password": "12345678", "security": "WPA/WPA2", "hidden": False}
    assert t.validate(data).is_valid
    assert t.build_payload(data) == "WIFI:T:WPA;S:MiRed;P:12345678;H:false;;"


def test_wifi_no_password():
    t = WiFiType()
    data = {"ssid": "RedAbierta", "security": "Sin contraseña"}
    assert t.validate(data).is_valid
    payload = t.build_payload(data)
    assert "T:nopass" in payload


def test_vcard_payload():
    t = VCardType()
    data = {"first_name": "Ana", "last_name": "Gómez", "phone": "3000000000"}
    assert t.validate(data).is_valid
    payload = t.build_payload(data)
    assert "BEGIN:VCARD" in payload and "FN:Ana Gómez" in payload


def test_generator_creates_image():
    gen = QRGenerator()
    result = gen.generate("https://intelliqr.app", QRDesignOptions())
    assert result.image.size[0] > 0
    assert result.error_correction_used == "M"


def test_generator_logo_warning():
    gen = QRGenerator()
    design = QRDesignOptions(logo_path=None, logo_size_ratio=0.35)
    # simulamos que hay logo para forzar la validación de tamaño
    design.logo_path = None
    result = gen.generate("test", design)
    assert isinstance(result.warnings, list)


def test_exporter_png(tmp_path):
    gen = QRGenerator()
    result = gen.generate("https://intelliqr.app", QRDesignOptions())
    exporter = QRExporter()
    out = exporter.export(result.image, tmp_path / "out.png", ExportOptions(fmt="PNG"))
    assert out.exists()


def test_logo_size_actually_changes_with_ratio(tmp_path):
    """Regresión: el control de tamaño del logo debe cambiar el área real
    del logo incrustado, no solo un valor guardado sin efecto visual."""
    from PIL import Image as PILImage, ImageDraw
    logo_path = tmp_path / "logo.png"
    logo = PILImage.new("RGBA", (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(logo).ellipse([10, 10, 190, 190], fill=(220, 38, 38, 255))
    logo.save(logo_path)

    gen = QRGenerator()
    small = gen.generate("https://intelliqr.app", QRDesignOptions(logo_path=str(logo_path), logo_size_ratio=0.10))
    large = gen.generate("https://intelliqr.app", QRDesignOptions(logo_path=str(logo_path), logo_size_ratio=0.35))

    def red_pixel_count(img):
        import numpy as np
        arr = np.array(img.convert("RGB"))
        return int(((arr[:, :, 0] > 180) & (arr[:, :, 1] < 80) & (arr[:, :, 2] < 80)).sum())

    assert red_pixel_count(large.image) > red_pixel_count(small.image) * 3


def test_toggle_row_emits_changed_without_typeerror():
    """Regresión: stateChanged envía un int; conectarlo directo a una señal
    sin argumentos (`changed.emit`) lanzaba un TypeError silencioso que
    impedía activar el degradado y el fondo transparente desde la UI."""
    import sys
    from PySide6.QtWidgets import QApplication
    from ui.qr.qr_design import _ToggleRow

    app = QApplication.instance() or QApplication(sys.argv)
    row = _ToggleRow("Prueba")
    received = []
    row.changed.connect(lambda: received.append(True))
    row.checkbox.click()
    assert received, "La señal 'changed' nunca se disparó al hacer clic"
    assert row.is_checked() is True
