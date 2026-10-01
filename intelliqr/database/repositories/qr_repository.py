"""Repositorio: aísla la lógica de negocio del acceso a datos (sección 48.12)."""
from __future__ import annotations
import json
from datetime import datetime

from sqlalchemy.orm import joinedload

from database.database import get_session
from database.models import QRCode, QRDesign


class QRRepository:
    def save(
        self,
        name: str,
        type_id: str,
        payload: str,
        content_data: dict,
        design_data: dict,
        thumbnail_path: str | None = None,
        qr_id: int | None = None,
    ) -> int:
        with get_session() as session:
            if qr_id:
                qr = session.get(QRCode, qr_id)
                if qr is None:
                    raise ValueError(f"QR con id {qr_id} no existe.")
                qr.name = name
                qr.type_id = type_id
                qr.payload = payload
                qr.content_data_json = json.dumps(content_data, ensure_ascii=False)
                qr.thumbnail_path = thumbnail_path
                qr.updated_at = datetime.utcnow()
            else:
                qr = QRCode(
                    name=name,
                    type_id=type_id,
                    payload=payload,
                    content_data_json=json.dumps(content_data, ensure_ascii=False),
                    thumbnail_path=thumbnail_path,
                )
                session.add(qr)
                session.flush()

            # Ojo: el diseño hay que añadirlo a la sesión cuando es nuevo.
            # Antes se creaba el QRDesign pero nunca se hacía session.add()
            # (la condición previa nunca se cumplía porque qr_code_id ya venía
            # relleno), así que el diseño no se guardaba nunca y al reabrir el
            # QR volvía a los valores por defecto.
            design = qr.design
            if design is None:
                design = QRDesign(qr_code_id=qr.id)
                qr.design = design
                session.add(design)
            design.pattern = design_data.get("pattern", "cuadrado")
            design.corner_style = design_data.get("corner_style", "cuadradas")
            design.fg_color = design_data.get("fg_color", "#0F172A")
            design.bg_color = design_data.get("bg_color", "#FFFFFF")
            design.gradient_enabled = design_data.get("gradient_enabled", False)
            design.gradient_start = design_data.get("gradient_start", "#2563EB")
            design.gradient_end = design_data.get("gradient_end", "#60A5FA")
            design.logo_path = design_data.get("logo_path")
            design.logo_size_ratio = design_data.get("logo_size_ratio", 0.22)
            design.box_size = design_data.get("box_size", 10)
            design.transparent_background = design_data.get("transparent_background", False)
            design.frame_style = design_data.get("frame_style", "ninguno")
            design.frame_text = design_data.get("frame_text", "ESCANÉAME")
            design.frame_color = design_data.get("frame_color", "#2563EB")
            design.frame_text_color = design_data.get("frame_text_color", "#FFFFFF")
            design.qr_code_id = qr.id

            session.commit()
            return qr.id

    def list_all(self) -> list[QRCode]:
        with get_session() as session:
            return list(
                session.query(QRCode)
                .options(joinedload(QRCode.design))
                .order_by(QRCode.updated_at.desc())
                .all()
            )

    def get(self, qr_id: int) -> QRCode | None:
        with get_session() as session:
            return (
                session.query(QRCode)
                .options(joinedload(QRCode.design))
                .filter(QRCode.id == qr_id)
                .first()
            )

    def delete(self, qr_id: int) -> None:
        with get_session() as session:
            qr = session.get(QRCode, qr_id)
            if qr:
                session.delete(qr)
                session.commit()

    def duplicate(self, qr_id: int, new_name: str) -> int:
        with get_session() as session:
            original = session.get(QRCode, qr_id)
            if original is None:
                raise ValueError("QR original no encontrado.")
            copy = QRCode(
                name=new_name,
                type_id=original.type_id,
                payload=original.payload,
                content_data_json=original.content_data_json,
                thumbnail_path=original.thumbnail_path,
            )
            session.add(copy)
            session.flush()
            if original.design:
                copy_design = QRDesign(
                    qr_code_id=copy.id,
                    pattern=original.design.pattern,
                    corner_style=original.design.corner_style,
                    fg_color=original.design.fg_color,
                    bg_color=original.design.bg_color,
                    gradient_enabled=original.design.gradient_enabled,
                    gradient_start=original.design.gradient_start,
                    gradient_end=original.design.gradient_end,
                    logo_path=original.design.logo_path,
                    logo_size_ratio=original.design.logo_size_ratio,
                    box_size=original.design.box_size,
                    transparent_background=original.design.transparent_background,
                    frame_style=original.design.frame_style,
                    frame_text=original.design.frame_text,
                    frame_color=original.design.frame_color,
                    frame_text_color=original.design.frame_text_color,
                )
                session.add(copy_design)
            session.commit()
            return copy.id
