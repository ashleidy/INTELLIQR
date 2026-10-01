from __future__ import annotations
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, Text, Boolean, ForeignKey, LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    qr_codes: Mapped[list["QRCode"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class QRCode(Base):
    __tablename__ = "qr_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    type_id: Mapped[str] = mapped_column(String(50))
    payload: Mapped[str] = mapped_column(Text)
    content_data_json: Mapped[str] = mapped_column(Text)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project: Mapped["Project | None"] = relationship(back_populates="qr_codes")
    design: Mapped["QRDesign | None"] = relationship(back_populates="qr_code", uselist=False, cascade="all, delete-orphan")


class QRDesign(Base):
    __tablename__ = "qr_designs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    qr_code_id: Mapped[int] = mapped_column(ForeignKey("qr_codes.id"))
    pattern: Mapped[str] = mapped_column(String(30), default="cuadrado")
    corner_style: Mapped[str] = mapped_column(String(30), default="cuadradas")
    fg_color: Mapped[str] = mapped_column(String(10), default="#0F172A")
    bg_color: Mapped[str] = mapped_column(String(10), default="#FFFFFF")
    gradient_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    gradient_start: Mapped[str] = mapped_column(String(10), default="#2563EB")
    gradient_end: Mapped[str] = mapped_column(String(10), default="#60A5FA")
    logo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_size_ratio: Mapped[float] = mapped_column(Float, default=0.22)
    transparent_background: Mapped[bool] = mapped_column(Boolean, default=False)
    frame_style: Mapped[str] = mapped_column(String(30), default="ninguno")
    frame_text: Mapped[str] = mapped_column(String(100), default="ESCANÉAME")
    frame_color: Mapped[str] = mapped_column(String(10), default="#2563EB")
    frame_text_color: Mapped[str] = mapped_column(String(10), default="#FFFFFF")
    box_size: Mapped[int] = mapped_column(Integer, default=10)

    qr_code: Mapped["QRCode"] = relationship(back_populates="design")


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))
    type_id: Mapped[str] = mapped_column(String(50))
    default_data_json: Mapped[str] = mapped_column(Text)
    default_design_json: Mapped[str] = mapped_column(Text)


class Barcode(Base):
    __tablename__ = "barcodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    barcode_type: Mapped[str] = mapped_column(String(30))
    value: Mapped[str] = mapped_column(String(200))
    image_scale: Mapped[int] = mapped_column(Integer, default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    width_mm: Mapped[float] = mapped_column(Float, default=50)
    height_mm: Mapped[float] = mapped_column(Float, default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    elements: Mapped[list["LabelElement"]] = relationship(back_populates="label", cascade="all, delete-orphan")


class LabelElement(Base):
    __tablename__ = "label_elements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label_id: Mapped[int] = mapped_column(ForeignKey("labels.id"))
    element_type: Mapped[str] = mapped_column(String(30))
    x: Mapped[float] = mapped_column(Float, default=0)
    y: Mapped[float] = mapped_column(Float, default=0)
    width: Mapped[float] = mapped_column(Float, default=10)
    height: Mapped[float] = mapped_column(Float, default=10)
    rotation: Mapped[float] = mapped_column(Float, default=0)
    content_json: Mapped[str] = mapped_column(Text, default="{}")

    label: Mapped["Label"] = relationship(back_populates="elements")


class Settings(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class Scan(Base):
    """Historial de códigos escaneados con la cámara (sección 26)."""
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_label: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)   # ← NUEVO
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)