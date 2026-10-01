"""
Configuración de la capa web de IntelliQR.

Orden de precedencia para cada valor:
  1. st.secrets  (Streamlit Cloud y .streamlit/secrets.toml en local)
  2. variables de entorno (útil para tests y para correr sin Streamlit)
  3. valor por defecto

Nunca se escriben credenciales en el código: ver .env.example y
.streamlit/secrets.toml.example.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger("intelliqr.config")


def _from_secrets(key: str) -> str | None:
    """Lee st.secrets sin reventar si Streamlit no está disponible o no hay
    archivo de secrets (caso típico al ejecutar los tests)."""
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key])
        # También admitimos una sección [intelliqr] para mantener el archivo ordenado.
        section = st.secrets.get("intelliqr", None)
        if section is not None and key in section:
            return str(section[key])
    except Exception:
        pass
    return None


def get_setting(key: str, default: str = "") -> str:
    value = _from_secrets(key)
    if value is None:
        value = os.environ.get(key)
    return (value if value is not None else default).strip()


@dataclass(frozen=True)
class AppConfig:
    google_script_url: str
    api_token: str
    request_timeout: int
    default_language: str

    @property
    def is_configured(self) -> bool:
        return bool(self.google_script_url)


def load_config() -> AppConfig:
    timeout_raw = get_setting("REQUEST_TIMEOUT", "20")
    try:
        timeout = max(5, min(int(timeout_raw), 60))
    except ValueError:
        timeout = 20

    return AppConfig(
        google_script_url=get_setting("GOOGLE_SCRIPT_URL"),
        api_token=get_setting("API_TOKEN"),
        request_timeout=timeout,
        default_language=get_setting("DEFAULT_LANGUAGE", "es") or "es",
    )
