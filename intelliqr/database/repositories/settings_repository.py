"""Repositorio de configuración (tabla settings: clave -> valor)."""
from __future__ import annotations
from database.database import get_session
from database.models import Settings


class SettingsRepository:
    def get(self, key: str, default: str | None = None) -> str | None:
        with get_session() as session:
            record = session.get(Settings, key)
            return record.value if record else default

    def set(self, key: str, value: str) -> None:
        with get_session() as session:
            record = session.get(Settings, key)
            if record:
                record.value = value
            else:
                record = Settings(key=key, value=value)
                session.add(record)
            session.commit()
