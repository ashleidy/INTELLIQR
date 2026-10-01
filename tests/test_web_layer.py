
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.apps_script import AppsScriptClient, BackendError  # noqa: E402
from services.database import AppsScriptDatabase, InMemoryDatabase, QRRecord, _as_bool  # noqa: E402
from utils.config import AppConfig  # noqa: E402
from utils.helpers import generate_qr_id, safe_filename, truncate  # noqa: E402
from utils.validators import validate_create_form, validate_qr_id, validate_url  # noqa: E402


def make_config(**overrides) -> AppConfig:
    base = dict(
        google_script_url="https://script.google.com/macros/s/AAA/exec",
        api_token="token-de-prueba",
        request_timeout=10,
        default_language="es",
    )
    base.update(overrides)
    return AppConfig(**base)


# ------------------------------------------------------------- validaciones
@pytest.mark.parametrize("url", [
    "https://restaurant.com/menu",
    "http://ejemplo.org",
    "https://sub.dominio.co.uk/ruta?x=1",
])
def test_urls_validas(url):
    assert validate_url(url) is None


@pytest.mark.parametrize("url", [
    "",
    "restaurant.com",
    "javascript:alert(1)",
    "data:text/html,<script>",
    "file:///etc/passwd",
    "ftp://servidor/archivo",
    "https://",
    "https://con espacio.com",
])
def test_urls_rechazadas(url):
    assert validate_url(url) is not None


def test_formulario_completo_reporta_todos_los_errores():
    errores = validate_create_form("", "no-es-una-url")
    assert len(errores) == 2


def test_validacion_de_identificador():
    assert validate_qr_id("A8X29K") is None
    assert validate_qr_id("a8x29k") is None  # se normaliza a mayúsculas
    assert validate_qr_id("AB") is not None
    assert validate_qr_id("A8X-29K") is not None


# ------------------------------------------------------------------ helpers
def test_identificadores_sin_caracteres_ambiguos():
    for _ in range(200):
        qr_id = generate_qr_id()
        assert len(qr_id) == 6
        assert not set(qr_id) & set("OIL01")


def test_identificadores_son_razonablemente_unicos():
    generados = {generate_qr_id() for _ in range(2000)}
    assert len(generados) > 1990


def test_nombre_de_archivo_seguro():
    assert safe_filename('menú: "verano"/2027') == "menú_ _verano__2027"
    assert safe_filename("") == "intelliqr"


def test_truncado():
    assert truncate("abcdefghij", 5) == "abcd…"
    assert truncate("abc", 5) == "abc"


def test_normalizacion_de_booleanos_de_la_hoja():
    assert _as_bool("TRUE") is True
    assert _as_bool("FALSE") is False
    assert _as_bool(True) is True
    assert _as_bool("") is True          # celda vacía = activo por defecto
    assert _as_bool("", default=False) is False


# ------------------------------------------------------ ciclo de vida del QR
def test_ciclo_completo_crear_editar_desactivar_reactivar():
    db = InMemoryDatabase()

    creado = db.create_qr("Menú Restaurante", "URL", "https://restaurant.com/menu",
                          descripcion="Menú principal")
    assert creado.activo is True
    assert len(creado.id) == 6

    # Editar el destino NO cambia el identificador: ese es el punto de todo
    # el proyecto — el QR impreso sigue sirviendo.
    editado = db.update_qr(creado.id, url_destino="https://restaurant.com/menu-2027")
    assert editado.id == creado.id
    assert editado.url_destino.endswith("menu-2027")

    desactivado = db.deactivate_qr(creado.id)
    assert desactivado.activo is False

    reactivado = db.activate_qr(creado.id)
    assert reactivado.activo is True

    # Desactivar es un borrado lógico: el registro sigue existiendo.
    assert db.get_qr(creado.id) is not None
    assert len(db.list_qrs()) == 1


def test_estadisticas_del_dashboard():
    db = InMemoryDatabase()
    for i in range(3):
        db.create_qr(f"QR {i}", "URL", "https://ejemplo.com")
    inactivo = db.create_qr("Inactivo", "URL", "https://ejemplo.com")
    db.deactivate_qr(inactivo.id)

    stats = db.stats()
    assert stats["total"] == 4
    assert stats["activos"] == 3
    assert stats["inactivos"] == 1


def test_actualizar_inexistente_da_error_amigable():
    with pytest.raises(BackendError):
        InMemoryDatabase().update_qr("NOEXIS", nombre="x")


# ------------------------------------------------- cliente HTTP (con dobles)
class FakeResponse:
    def __init__(self, payload=None, status_code=200, text=""):
        self._payload = payload
        self.status_code = status_code
        self.text = text or ""

    def json(self):
        if self._payload is None:
            raise ValueError("no es JSON")
        return self._payload


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.last_body = None

    def post(self, url, data=None, headers=None, timeout=None, allow_redirects=True):
        import json as _json

        self.last_body = _json.loads(data)
        if self.exc:
            raise self.exc
        return self.response


def test_el_token_viaja_en_cada_peticion():
    session = FakeSession(FakeResponse({"ok": True, "data": {"status": "ok"}}))
    AppsScriptClient(make_config(), session=session).call("ping")
    assert session.last_body["token"] == "token-de-prueba"
    assert session.last_body["action"] == "ping"


def test_timeout_se_traduce_a_mensaje_amigable():
    import requests

    session = FakeSession(exc=requests.Timeout("tardó demasiado"))
    with pytest.raises(BackendError) as excinfo:
        AppsScriptClient(make_config(), session=session).call("ping")
    assert "Intenta nuevamente" in excinfo.value.user_message
    assert "tardó demasiado" in excinfo.value.technical  # el detalle no se pierde


def test_respuesta_html_en_vez_de_json_se_explica():
    session = FakeSession(FakeResponse(None, text="<html>Sign in to continue</html>"))
    with pytest.raises(BackendError) as excinfo:
        AppsScriptClient(make_config(), session=session).call("ping")
    assert "Cualquier persona" in excinfo.value.user_message


def test_sin_url_configurada_no_se_intenta_la_llamada():
    session = FakeSession(FakeResponse({"ok": True, "data": {}}))
    with pytest.raises(BackendError):
        AppsScriptClient(make_config(google_script_url=""), session=session).call("ping")
    assert session.last_body is None


def test_error_de_negocio_del_backend_llega_al_usuario():
    session = FakeSession(FakeResponse({"ok": False, "error": "QR no encontrado."}))
    with pytest.raises(BackendError) as excinfo:
        AppsScriptClient(make_config(), session=session).call("get_qr", {"id": "XXXXXX"})
    assert excinfo.value.user_message == "QR no encontrado."


def test_get_qr_inexistente_devuelve_none_no_excepcion():
    session = FakeSession(FakeResponse({"ok": False, "error": "QR no encontrado."}))
    db = AppsScriptDatabase(AppsScriptClient(make_config(), session=session))
    assert db.get_qr("XXXXXX") is None


def test_update_solo_envia_campos_permitidos():
    session = FakeSession(FakeResponse({"ok": True, "data": {"id": "A8X29K"}}))
    db = AppsScriptDatabase(AppsScriptClient(make_config(), session=session))
    db.update_qr("A8X29K", nombre="Nuevo", tipo="HACK", id="OTRO", activo=False)
    assert session.last_body["id"] == "A8X29K"       # el id no se puede suplantar
    assert session.last_body["nombre"] == "Nuevo"
    assert "tipo" not in session.last_body           # campo no editable, descartado


def test_registro_normaliza_lo_que_venga_de_la_hoja():
    session = FakeSession(FakeResponse({"ok": True, "data": {
        "id": " A8X29K ", "nombre": "Menú", "activo": "TRUE", "dinamico": "FALSE",
    }}))
    db = AppsScriptDatabase(AppsScriptClient(make_config(), session=session))
    record = db.get_qr("A8X29K")
    assert isinstance(record, QRRecord)
    assert record.id == "A8X29K"
    assert record.activo is True
    assert record.dinamico is False
    assert record.estado_label.endswith("Activo")
