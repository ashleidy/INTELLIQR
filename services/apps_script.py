"""
Cliente HTTP del backend (Google Apps Script Web App).

Responsabilidades:
  - hablar con la Web App vía POST JSON (Apps Script sólo expone doGet/doPost,
    así que las operaciones tipo PUT/DELETE viajan como una acción dentro del
    cuerpo: {"action": "update_qr", ...});
  - traducir CUALQUIER fallo (timeout, DNS, HTML de error de Google, JSON
    inválido, error de negocio) en una BackendError con mensaje amigable,
    dejando el detalle técnico en el log (sección 19 del spec).

Esta clase no sabe nada de Streamlit ni de QR: sólo transporte.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import requests

from utils.config import AppConfig

logger = logging.getLogger("intelliqr.apps_script")

FRIENDLY_GENERIC = "No fue posible conectar con el servidor. Intenta nuevamente."
FRIENDLY_TIMEOUT = "El servidor tardó demasiado en responder. Intenta nuevamente."
FRIENDLY_UNCONFIGURED = (
    "IntelliQR todavía no está conectado a tu backend. "
    "Configura GOOGLE_SCRIPT_URL en Configuración para guardar el historial."
)


class BackendError(Exception):
    """Error listo para mostrarle al usuario. El detalle técnico va al log."""

    def __init__(self, user_message: str, technical: str | None = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.technical = technical or user_message


class AppsScriptClient:
    def __init__(self, config: AppConfig, session: requests.Session | None = None):
        self.config = config
        self._session = session or requests.Session()

    # ---------------------------------------------------------------- core
    def call(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.config.is_configured:
            raise BackendError(FRIENDLY_UNCONFIGURED, "GOOGLE_SCRIPT_URL vacío")

        body = dict(payload or {})
        body["action"] = action
        if self.config.api_token:
            body["token"] = self.config.api_token

        try:
            response = self._session.post(
                self.config.google_script_url,
                data=json.dumps(body),
                headers={"Content-Type": "application/json"},
                timeout=self.config.request_timeout,
                # Apps Script responde 302 hacia googleusercontent: el script
                # YA se ejecutó, el redirect sólo entrega la salida.
                allow_redirects=True,
            )
        except requests.Timeout as exc:
            logger.warning("Timeout llamando a Apps Script (%s): %s", action, exc)
            raise BackendError(FRIENDLY_TIMEOUT, str(exc)) from exc
        except requests.RequestException as exc:
            logger.warning("Fallo de red llamando a Apps Script (%s): %s", action, exc)
            raise BackendError(FRIENDLY_GENERIC, str(exc)) from exc

        if response.status_code >= 400:
            logger.warning("Apps Script devolvió HTTP %s en %s", response.status_code, action)
            if response.status_code in (401, 403):
                raise BackendError(
                    "El servidor rechazó la petición. Revisa el token y los permisos "
                    "de la Web App (debe estar publicada para «Cualquier persona»).",
                    f"HTTP {response.status_code}",
                )
            raise BackendError(FRIENDLY_GENERIC, f"HTTP {response.status_code}: {response.text[:400]}")

        try:
            data = response.json()
        except ValueError as exc:
            # Caso clásico: la Web App no está publicada como "Cualquier persona"
            # y Google devuelve una página HTML de login en vez de JSON.
            snippet = response.text[:400]
            logger.warning("Respuesta no-JSON de Apps Script (%s): %s", action, snippet)
            raise BackendError(
                "El servidor respondió algo inesperado. Suele significar que la Web App "
                "no está publicada con acceso «Cualquier persona» o que la URL no termina en /exec.",
                snippet,
            ) from exc

        if not isinstance(data, dict):
            raise BackendError(FRIENDLY_GENERIC, f"Respuesta inesperada: {data!r}")

        if not data.get("ok", False):
            message = str(data.get("error") or FRIENDLY_GENERIC)
            logger.info("Apps Script rechazó %s: %s", action, message)
            raise BackendError(message, message)

        result = data.get("data")
        return result if isinstance(result, dict) else {"result": result}

    # ------------------------------------------------------------- health
    def ping(self) -> dict[str, Any]:
        """Prueba de conexión usada por la pantalla de Configuración."""
        return self.call("ping")
