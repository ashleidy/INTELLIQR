
from __future__ import annotations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session

from app.config import DATABASE_URL
from database.models import Base

_engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, future=True)


def _run_lightweight_migrations() -> None:
    
    inspector = inspect(_engine)
    existing_tables = set(inspector.get_table_names())

    with _engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue  # tabla nueva: create_all ya la crea completa

            existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue

                col_type = column.type.compile(dialect=_engine.dialect)
                default_clause = ""
                if column.default is not None and getattr(column.default, "is_scalar", False):
                    value = column.default.arg
                    if isinstance(value, bool):
                        value = int(value)
                    if isinstance(value, str):
                        default_clause = f" DEFAULT '{value}'"
                    elif value is not None:
                        default_clause = f" DEFAULT {value}"

                conn.execute(text(
                    f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}{default_clause}'
                ))


def init_db() -> None:
    """Crea las tablas que falten y migra las que ya existan. Se llama una vez al arrancar la app."""
    Base.metadata.create_all(_engine)
    _run_lightweight_migrations()


def get_session() -> Session:
    return SessionLocal()
