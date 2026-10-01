
from __future__ import annotations
import re
from typing import Any
from .base import QRType, ValidationResult

_IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$")


class SEPATransferType(QRType):
    type_id = "sepa"
    display_name = "Transferencia SEPA"
    category = "Banca"
    description = "QR bancario (EPC/Girocode) que prellena una transferencia SEPA."
    icon = "bank"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        name = (data.get("beneficiary_name") or "").strip()
        iban = (data.get("iban") or "").strip().replace(" ", "").upper()
        amount = (data.get("amount") or "").strip()

        if not name:
            return ValidationResult.fail("beneficiary_name", "Introduce el nombre del beneficiario.")
        if len(name) > 70:
            return ValidationResult.fail("beneficiary_name", "El nombre no puede superar los 70 caracteres.")
        if not iban or not _IBAN_RE.match(iban):
            return ValidationResult.fail("iban", "Introduce un IBAN válido, ej. ES9121000418450200051332.")
        if amount:
            try:
                value = float(amount.replace(",", "."))
                if value <= 0:
                    raise ValueError
            except ValueError:
                return ValidationResult.fail("amount", "El monto debe ser un número positivo, ej. 25.50.")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        name = data["beneficiary_name"].strip()[:70]
        iban = data["iban"].strip().replace(" ", "").upper()
        bic = (data.get("bic") or "").strip().upper()
        amount = (data.get("amount") or "").strip().replace(",", ".")
        reference = (data.get("reference") or "").strip()[:35]
        concept = (data.get("concept") or "").strip()[:140]

        amount_field = f"EUR{float(amount):.2f}" if amount else ""

        lines = [
            "BCD",           # cabecera del servicio
            "002",           # versión
            "1",             # codificación de caracteres (UTF-8)
            "SCT",           # SEPA Credit Transfer
            bic,             # BIC (opcional desde 2016 dentro de la UE)
            name,            # beneficiario
            iban,            # IBAN
            amount_field,    # monto (opcional)
            "",              # código de propósito (no usado)
            reference,       # referencia estructurada (opcional)
            concept,         # concepto / texto libre (opcional)
        ]
        return "\n".join(lines)
