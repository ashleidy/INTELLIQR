"""Estado compartido entre páginas de Streamlit (configuración, base de datos,
caché de la lista de QR y presentación uniforme de errores)."""
from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

import streamlit as st

from services.apps_script import BackendError
from services.database import Database, QRRecord, build_database
from utils.config import AppConfig, load_config

logger = logging.getLogger("intelliqr.state")

T = TypeVar("T")


def get_config() -> AppConfig:
    if "iq_config" not in st.session_state:
        st.session_state["iq_config"] = load_config()
    return st.session_state["iq_config"]


def reload_config() -> AppConfig:
    st.session_state.pop("iq_config", None)
    st.session_state.pop("iq_db", None)
    clear_qr_cache()
    return get_config()


def get_db() -> Database:
    if "iq_db" not in st.session_state:
        st.session_state["iq_db"] = build_database(get_config())
    return st.session_state["iq_db"]


# ------------------------------------------------------------------- caché
def list_qrs(force: bool = False) -> list[QRRecord]:
    """Lista cacheada en sesión: cada llamada a la API de Sheets cuesta
    ~1-2 s, así que no se repite en cada rerun de Streamlit."""
    if force:
        clear_qr_cache()
    if "iq_qrs" not in st.session_state:
        st.session_state["iq_qrs"] = get_db().list_qrs()
    return st.session_state["iq_qrs"]


def clear_qr_cache() -> None:
    st.session_state.pop("iq_qrs", None)


# ------------------------------------------------------------ errores (§19)
def guard(operation: Callable[[], T], *, spinner: str = "Conectando…") -> T | None:
    """Ejecuta una operación contra el backend mostrando un mensaje amigable
    si falla. El detalle técnico va al log, nunca a la pantalla."""
    try:
        with st.spinner(spinner):
            return operation()
    except BackendError as exc:
        logger.error("Backend error: %s", exc.technical)
        st.error(exc.user_message)
    except Exception as exc:  # noqa: BLE001 — último cortafuegos de la UI
        logger.exception("Error inesperado en la interfaz: %s", exc)
        st.error("Ocurrió un error inesperado. Intenta nuevamente.")
    return None


def require_backend() -> bool:
    """Avisa (sin bloquear) cuando la app corre sin backend configurado."""
    if get_config().is_configured:
        return True
    st.info(
        "Estás en **modo demo**: los códigos que crees se guardan sólo en esta sesión "
        "y se pierden al recargar. Conecta tu Google Apps Script en **Configuración** "
        "para guardar el historial de forma permanente.",
        icon="🧪",
    )
    return False
