"""Tests del tipo de QR de transferencia SEPA (Banca electrónica)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qr_types.sepa import SEPATransferType


def test_sepa_valid():
    t = SEPATransferType()
    data = {"beneficiary_name": "IntelliQR SAS", "iban": "ES9121000418450200051332", "amount": "25.50"}
    result = t.validate(data)
    assert result.is_valid
    payload = t.build_payload(data)
    assert payload.startswith("BCD\n002\n1\nSCT")
    assert "ES9121000418450200051332" in payload
    assert "EUR25.50" in payload


def test_sepa_invalid_iban():
    t = SEPATransferType()
    data = {"beneficiary_name": "IntelliQR SAS", "iban": "no-es-un-iban"}
    assert not t.validate(data).is_valid


def test_sepa_missing_name():
    t = SEPATransferType()
    data = {"iban": "ES9121000418450200051332"}
    assert not t.validate(data).is_valid


def test_sepa_without_amount_is_optional():
    t = SEPATransferType()
    data = {"beneficiary_name": "IntelliQR SAS", "iban": "ES9121000418450200051332"}
    assert t.validate(data).is_valid
    payload = t.build_payload(data)
    lines = payload.split("\n")
    assert lines[7] == ""  # línea del monto vacía cuando no se especifica
