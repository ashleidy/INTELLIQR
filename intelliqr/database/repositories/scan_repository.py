"""Repositorio del historial de códigos escaneados."""
from __future__ import annotations
from io import BytesIO

from PIL import Image

from database.database import get_session
from database.models import Scan


class ScanRepository:
    def save(self, type_label: str, content: str,
             image: Image.Image | None = None) -> int:
        """Guarda un escaneo. Si `image` viene dada, se persiste como PNG
        en la columna BLOB `Scan.image` para poder mostrarla en el historial."""
        blob: bytes | None = None
        if image is not None:
            buf = BytesIO()
            image.convert("RGB").save(buf, format="PNG")
            blob = buf.getvalue()

        with get_session() as session:
            record = Scan(type_label=type_label, content=content, image=blob)
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id

    def list_recent(self, limit: int = 20) -> list[Scan]:
        """Compatibilidad con el código existente (p. ej. el Home anterior)."""
        with get_session() as session:
            return list(
                session.query(Scan)
                .order_by(Scan.created_at.desc())
                .limit(limit)
                .all()
            )

    def list_all(self) -> list[Scan]:
        """Todos los escaneos, más recientes primero. Usado por HistoryScreen."""
        with get_session() as session:
            return list(
                session.query(Scan).order_by(Scan.created_at.desc()).all()
            )

    def get(self, scan_id: int) -> Scan | None:
        with get_session() as session:
            return session.get(Scan, scan_id)

    def delete(self, scan_id: int) -> None:
        with get_session() as session:
            record = session.get(Scan, scan_id)
            if record is not None:
                session.delete(record)
                session.commit()