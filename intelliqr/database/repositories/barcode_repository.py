"""Repositorio de códigos de barras guardados."""
from __future__ import annotations
from database.database import get_session
from database.models import Barcode


class BarcodeRepository:
    def list_all(self) -> list[Barcode]:
        with get_session() as session:
            return list(session.query(Barcode).order_by(Barcode.created_at.desc()).all())

    def get(self, barcode_id: int) -> Barcode | None:
        with get_session() as session:
            return session.get(Barcode, barcode_id)

    def save(self, name: str, barcode_type: str, value: str, barcode_id: int | None = None, image_scale: int = 2) -> int:
        with get_session() as session:
            if barcode_id:
                record = session.get(Barcode, barcode_id)
                if record is None:
                    raise ValueError(f"Código de barras con id {barcode_id} no existe.")
                record.name = name
                record.barcode_type = barcode_type
                record.value = value
                record.image_scale = image_scale
            else:
                record = Barcode(name=name, barcode_type=barcode_type, value=value, image_scale=image_scale)
                session.add(record)
            session.commit()
            return record.id

    def delete(self, barcode_id: int) -> None:
        with get_session() as session:
            record = session.get(Barcode, barcode_id)
            if record:
                session.delete(record)
                session.commit()

    def duplicate(self, barcode_id: int, new_name: str) -> int:
        with get_session() as session:
            original = session.get(Barcode, barcode_id)
            if original is None:
                raise ValueError("Código de barras original no encontrado.")
            copy = Barcode(name=new_name, barcode_type=original.barcode_type, value=original.value)
            session.add(copy)
            session.commit()
            return copy.id
