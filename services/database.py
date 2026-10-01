"""
Capa de abstracción de datos (sección 17 del spec).

La aplicación NUNCA habla con Google Sheets ni con Apps Script directamente:
habla con `Database`. Hoy la implementación concreta es AppsScriptDatabase;
mañana puede ser SupabaseDatabase sin tocar las páginas de Streamlit.

Deliberadamente conserva la forma del QRRepository que ya existía en la app
de escritorio (save / get / list / delete), para que el salto conceptual sea
mínimo para quien ya conocía el proyecto.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from services.apps_script import AppsScriptClient, BackendError
from utils.config import AppConfig

logger = logging.getLogger("intelliqr.database")


@dataclass
class QRRecord:
    """Un registro de la hoja QR_CODES, ya normalizado."""

    id: str
    nombre: str
    tipo: str
    url_destino: str
    activo: bool = True
    fecha_creacion: str = ""
    fecha_actualizacion: str = ""
    descripcion: str = ""
    dinamico: bool = False
    design_json: str = ""

    @property
    def estado_label(self) -> str:
        return "🟢 Activo" if self.activo else "🔴 Inactivo"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return default
    return str(value).strip().upper() in ("TRUE", "1", "SI", "SÍ", "YES", "ACTIVO")


def _record_from_payload(payload: dict[str, Any]) -> QRRecord:
    return QRRecord(
        id=str(payload.get("id", "")).strip(),
        nombre=str(payload.get("nombre", "")),
        tipo=str(payload.get("tipo", "URL")),
        url_destino=str(payload.get("url_destino", "")),
        activo=_as_bool(payload.get("activo")),
        fecha_creacion=str(payload.get("fecha_creacion", "")),
        fecha_actualizacion=str(payload.get("fecha_actualizacion", "")),
        descripcion=str(payload.get("descripcion", "")),
        dinamico=_as_bool(payload.get("dinamico"), False),
        design_json=str(payload.get("design_json", "") or ""),
    )


class Database(ABC):
    """Contrato que debe cumplir cualquier backend de datos de IntelliQR."""

    @abstractmethod
    def create_qr(self, nombre: str, tipo: str, url_destino: str,
                  descripcion: str = "", dinamico: bool = False,
                  design_json: str = "") -> QRRecord: ...

    @abstractmethod
    def get_qr(self, qr_id: str) -> QRRecord | None: ...

    @abstractmethod
    def list_qrs(self) -> list[QRRecord]: ...

    @abstractmethod
    def update_qr(self, qr_id: str, **fields: Any) -> QRRecord: ...

    @abstractmethod
    def deactivate_qr(self, qr_id: str) -> QRRecord: ...

    @abstractmethod
    def activate_qr(self, qr_id: str) -> QRRecord: ...

    # Utilidad común a todas las implementaciones
    def stats(self) -> dict[str, Any]:
        records = self.list_qrs()
        activos = sum(1 for r in records if r.activo)
        return {
            "total": len(records),
            "activos": activos,
            "inactivos": len(records) - activos,
            "recientes": sorted(records, key=lambda r: r.fecha_creacion, reverse=True)[:5],
        }


class AppsScriptDatabase(Database):
    """Implementación actual: Apps Script → Google Sheets."""

    def __init__(self, client: AppsScriptClient):
        self.client = client

    def create_qr(self, nombre: str, tipo: str, url_destino: str,
                  descripcion: str = "", dinamico: bool = False,
                  design_json: str = "") -> QRRecord:
        data = self.client.call("create_qr", {
            "nombre": nombre,
            "tipo": tipo,
            "url_destino": url_destino,
            "descripcion": descripcion,
            "dinamico": dinamico,
            "design_json": design_json,
        })
        return _record_from_payload(data)

    def get_qr(self, qr_id: str) -> QRRecord | None:
        try:
            data = self.client.call("get_qr", {"id": qr_id})
        except BackendError as exc:
            if "no encontrado" in exc.user_message.lower():
                return None
            raise
        return _record_from_payload(data)

    def list_qrs(self) -> list[QRRecord]:
        data = self.client.call("list_qrs")
        items = data.get("items") or data.get("result") or []
        return [_record_from_payload(item) for item in items if isinstance(item, dict)]

    def update_qr(self, qr_id: str, **fields: Any) -> QRRecord:
        allowed = {"nombre", "url_destino", "activo", "descripcion", "design_json"}
        payload = {k: v for k, v in fields.items() if k in allowed}
        payload["id"] = qr_id
        data = self.client.call("update_qr", payload)
        return _record_from_payload(data)

    def deactivate_qr(self, qr_id: str) -> QRRecord:
        # Borrado lógico, nunca físico (sección 5 del spec).
        return self.update_qr(qr_id, activo=False)

    def activate_qr(self, qr_id: str) -> QRRecord:
        return self.update_qr(qr_id, activo=True)


class InMemoryDatabase(Database):
    """Backend de respaldo para tests y para probar la interfaz sin backend.

    No persiste nada entre reinicios: sirve para desarrollo local y para que
    la suite de tests no necesite red.
    """

    def __init__(self) -> None:
        self._rows: dict[str, QRRecord] = {}
        self._counter = 0

    def _next_id(self) -> str:
        from utils.helpers import generate_qr_id

        for _ in range(50):
            candidate = generate_qr_id()
            if candidate not in self._rows:
                return candidate
        raise BackendError("No fue posible generar un identificador único.")

    def create_qr(self, nombre: str, tipo: str, url_destino: str,
                  descripcion: str = "", dinamico: bool = False,
                  design_json: str = "") -> QRRecord:
        now = datetime.now().isoformat(timespec="seconds")
        record = QRRecord(
            id=self._next_id(), nombre=nombre, tipo=tipo, url_destino=url_destino,
            activo=True, fecha_creacion=now, fecha_actualizacion=now,
            descripcion=descripcion, dinamico=dinamico, design_json=design_json,
        )
        self._rows[record.id] = record
        return record

    def get_qr(self, qr_id: str) -> QRRecord | None:
        return self._rows.get(qr_id)

    def list_qrs(self) -> list[QRRecord]:
        return sorted(self._rows.values(), key=lambda r: r.fecha_actualizacion, reverse=True)

    def update_qr(self, qr_id: str, **fields: Any) -> QRRecord:
        record = self._rows.get(qr_id)
        if record is None:
            raise BackendError("QR no encontrado.")
        for key in ("nombre", "url_destino", "activo", "descripcion", "design_json"):
            if key in fields:
                setattr(record, key, fields[key])
        record.fecha_actualizacion = datetime.now().isoformat(timespec="seconds")
        return record

    def deactivate_qr(self, qr_id: str) -> QRRecord:
        return self.update_qr(qr_id, activo=False)

    def activate_qr(self, qr_id: str) -> QRRecord:
        return self.update_qr(qr_id, activo=True)


class SupabaseDatabase(Database):
    """Hueco reservado para la migración futura a Supabase/PostgreSQL.

    Cuando llegue el momento, sólo hay que implementar estos cinco métodos y
    cambiar `get_database()`: ninguna página de Streamlit se entera.
    """

    _MSG = "El backend Supabase todavía no está implementado."

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:  # pragma: no cover
        raise NotImplementedError(self._MSG)

    def create_qr(self, *a: Any, **k: Any) -> QRRecord: raise NotImplementedError(self._MSG)
    def get_qr(self, qr_id: str) -> QRRecord | None: raise NotImplementedError(self._MSG)
    def list_qrs(self) -> list[QRRecord]: raise NotImplementedError(self._MSG)
    def update_qr(self, qr_id: str, **fields: Any) -> QRRecord: raise NotImplementedError(self._MSG)
    def deactivate_qr(self, qr_id: str) -> QRRecord: raise NotImplementedError(self._MSG)
    def activate_qr(self, qr_id: str) -> QRRecord: raise NotImplementedError(self._MSG)


def build_database(config: AppConfig) -> Database:
    """Fábrica: elige la implementación según la configuración disponible."""
    if config.is_configured:
        return AppsScriptDatabase(AppsScriptClient(config))
    logger.info("Sin GOOGLE_SCRIPT_URL: usando InMemoryDatabase (modo demo).")
    return InMemoryDatabase()
