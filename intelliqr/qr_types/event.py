from __future__ import annotations
from datetime import datetime
from typing import Any
from .base import QRType, ValidationResult


class EventType(QRType):
    type_id = "event"
    display_name = "Evento"
    category = "Eventos"
    description = "Agrega un evento directamente al calendario del asistente."
    icon = "calendar"

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        name = (data.get("name") or "").strip()
        if not name:
            return ValidationResult.fail("name", "Introduce el nombre del evento.")
        date = (data.get("date") or "").strip()
        if not date:
            return ValidationResult.fail("date", "Introduce la fecha del evento (AAAA-MM-DD).")
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return ValidationResult.fail("date", "La fecha debe tener el formato AAAA-MM-DD.")
        return ValidationResult.ok()

    def build_payload(self, data: dict[str, Any]) -> str:
        name = data["name"].strip()
        date = data["date"].strip().replace("-", "")
        time = (data.get("time") or "0000").strip().replace(":", "")
        location = (data.get("location") or "").strip()
        description = (data.get("description") or "").strip()
        url = (data.get("url") or "").strip()
        dtstamp = f"{date}T{time.ljust(4, '0')}00"
        lines = [
            "BEGIN:VEVENT",
            f"SUMMARY:{name}",
            f"DTSTART:{dtstamp}",
        ]
        if location:
            lines.append(f"LOCATION:{location}")
        if description:
            lines.append(f"DESCRIPTION:{description}")
        if url:
            lines.append(f"URL:{url}")
        lines.append("END:VEVENT")
        return "\n".join(lines)
