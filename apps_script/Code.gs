/**
 * IntelliQR — Backend (Google Apps Script Web App)
 * =================================================
 *
 * Hace dos trabajos distintos en un solo despliegue:
 *
 *   1) API JSON para la app Streamlit        →  doPost()
 *   2) Redirección de los QR dinámicos       →  doGet()?r=A8X29K
 *
 * CONFIGURACIÓN (una sola vez, antes de publicar):
 *   Extensiones → Apps Script → ⚙ Configuración del proyecto →
 *   Propiedades de la secuencia de comandos:
 *
 *     SHEET_ID    = el id de tu hoja de cálculo (está en su URL)
 *     API_TOKEN   = una cadena larga y aleatoria, la misma que pondrás en
 *                   los secrets de Streamlit
 *
 * NUNCA escribas el token aquí dentro.
 */

// ---------------------------------------------------------------- constantes
var SHEET_QR = 'QR_CODES';
var SHEET_USERS = 'USUARIOS';
var SHEET_SCANS = 'SCANS';

var QR_HEADERS = [
  'id', 'nombre', 'tipo', 'url_destino', 'activo',
  'fecha_creacion', 'fecha_actualizacion', 'descripcion',
  'dinamico', 'design_json'
];
var USER_HEADERS = ['id', 'email', 'nombre', 'plan', 'activo', 'fecha_registro'];
var SCAN_HEADERS = ['id', 'qr_id', 'fecha', 'hora', 'user_agent', 'ip', 'referer'];

// Alfabeto sin caracteres ambiguos (0/O, 1/I/L).
var ID_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
var ID_LENGTH = 6;

// ------------------------------------------------------------------ utilidades
function props_() {
  return PropertiesService.getScriptProperties();
}

function openSheet_(name, headers) {
  var id = props_().getProperty('SHEET_ID');
  if (!id) throw new Error('Falta la propiedad SHEET_ID en el proyecto de Apps Script.');
  var ss = SpreadsheetApp.openById(id);
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.appendRow(headers);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function jsonOut_(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

function ok_(data) { return jsonOut_({ ok: true, data: data }); }
function fail_(message) { return jsonOut_({ ok: false, error: String(message) }); }

function checkToken_(body) {
  var expected = props_().getProperty('API_TOKEN');
  if (!expected) return; // sin token configurado, la API queda abierta (no recomendado)
  if (String(body.token || '') !== expected) {
    throw new Error('Token inválido.');
  }
}

function nowParts_() {
  var tz = Session.getScriptTimeZone() || 'UTC';
  var now = new Date();
  return {
    iso: Utilities.formatDate(now, tz, "yyyy-MM-dd'T'HH:mm:ss"),
    fecha: Utilities.formatDate(now, tz, 'yyyy-MM-dd'),
    hora: Utilities.formatDate(now, tz, 'HH:mm:ss')
  };
}

function rowToObject_(headers, row) {
  var obj = {};
  for (var i = 0; i < headers.length; i++) {
    obj[headers[i]] = row[i];
  }
  obj.id = String(obj.id || '').trim();
  obj.activo = normalizeBool_(obj.activo, true);
  obj.dinamico = normalizeBool_(obj.dinamico, true);
  return obj;
}

function normalizeBool_(value, fallback) {
  if (value === true || value === false) return value;
  if (value === '' || value === null || value === undefined) return fallback;
  var text = String(value).trim().toUpperCase();
  return text === 'TRUE' || text === '1' || text === 'SI' || text === 'SÍ' || text === 'YES';
}

function readAll_() {
  var sheet = openSheet_(SHEET_QR, QR_HEADERS);
  var values = sheet.getDataRange().getValues();
  if (values.length < 2) return { sheet: sheet, headers: QR_HEADERS, rows: [] };
  var headers = values[0].map(function (h) { return String(h).trim(); });
  var rows = [];
  for (var i = 1; i < values.length; i++) {
    if (!String(values[i][0] || '').trim()) continue;
    rows.push({ rowNumber: i + 1, data: rowToObject_(headers, values[i]) });
  }
  return { sheet: sheet, headers: headers, rows: rows };
}

function findRow_(qrId) {
  var all = readAll_();
  var target = String(qrId || '').trim().toUpperCase();
  for (var i = 0; i < all.rows.length; i++) {
    if (String(all.rows[i].data.id).toUpperCase() === target) {
      return { sheet: all.sheet, headers: all.headers, rowNumber: all.rows[i].rowNumber, data: all.rows[i].data };
    }
  }
  return null;
}

function generateId_(existingIds) {
  for (var attempt = 0; attempt < 100; attempt++) {
    var id = '';
    for (var i = 0; i < ID_LENGTH; i++) {
      id += ID_ALPHABET.charAt(Math.floor(Math.random() * ID_ALPHABET.length));
    }
    if (existingIds.indexOf(id) === -1) return id;
  }
  throw new Error('No fue posible generar un identificador único.');
}

function assertSafeUrl_(url) {
  var text = String(url || '').trim();
  if (!text) throw new Error('La URL de destino es obligatoria.');
  if (!/^https?:\/\//i.test(text)) {
    throw new Error('Sólo se permiten direcciones http:// o https://.');
  }
  return text;
}

// ------------------------------------------------------------------- API POST
function doPost(e) {
  try {
    var body = {};
    if (e && e.postData && e.postData.contents) {
      body = JSON.parse(e.postData.contents);
    }
    checkToken_(body);

    switch (String(body.action || '')) {
      case 'ping':      return ok_(apiPing_());
      case 'create_qr': return ok_(apiCreateQr_(body));
      case 'get_qr':    return ok_(apiGetQr_(body));
      case 'list_qrs':  return ok_({ items: apiListQrs_() });
      case 'update_qr': return ok_(apiUpdateQr_(body));
      case 'list_scans': return ok_({ items: apiListScans_(body) });
      default:
        return fail_('Acción no reconocida.');
    }
  } catch (err) {
    return fail_(err && err.message ? err.message : err);
  }
}

// Permite probar la API desde el navegador: .../exec?action=ping
function doGet(e) {
  var params = (e && e.parameter) ? e.parameter : {};

  // 1) Redirección de QR dinámico — el caso que importa de verdad.
  var qrId = params.r || params.id;
  if (qrId) {
    return handleRedirect_(qrId, e);
  }

  // 2) Comprobación rápida de salud.
  if (params.action === 'ping') {
    try {
      return ok_(apiPing_());
    } catch (err) {
      return fail_(err.message);
    }
  }

  return HtmlService.createHtmlOutput(
    '<p style="font-family:system-ui;padding:24px">IntelliQR backend activo.</p>'
  );
}

// --------------------------------------------------------------- operaciones
function apiPing_() {
  var all = readAll_();
  ensureSupportSheets_();
  return { status: 'ok', total_qr: all.rows.length, timezone: Session.getScriptTimeZone() };
}

function ensureSupportSheets_() {
  openSheet_(SHEET_USERS, USER_HEADERS);
  openSheet_(SHEET_SCANS, SCAN_HEADERS);
}

function apiCreateQr_(body) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000); // evita que dos creaciones simultáneas generen el mismo id
  try {
    var all = readAll_();
    var existing = all.rows.map(function (r) { return String(r.data.id).toUpperCase(); });
    var id = generateId_(existing);
    var t = nowParts_();

    var dinamico = body.dinamico === undefined ? true : normalizeBool_(body.dinamico, true);
    var destino = dinamico ? assertSafeUrl_(body.url_destino) : String(body.url_destino || '');

    var record = {
      id: id,
      nombre: String(body.nombre || '').trim() || 'Sin nombre',
      tipo: String(body.tipo || 'URL'),
      url_destino: destino,
      activo: true,
      fecha_creacion: t.iso,
      fecha_actualizacion: t.iso,
      descripcion: String(body.descripcion || ''),
      dinamico: dinamico,
      design_json: String(body.design_json || '')
    };

    var row = QR_HEADERS.map(function (h) { return record[h]; });
    all.sheet.appendRow(row);
    return record;
  } finally {
    lock.releaseLock();
  }
}

function apiGetQr_(body) {
  var found = findRow_(body.id);
  if (!found) throw new Error('QR no encontrado.');
  return found.data;
}

function apiListQrs_() {
  return readAll_().rows.map(function (r) { return r.data; });
}

function apiUpdateQr_(body) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var found = findRow_(body.id);
    if (!found) throw new Error('QR no encontrado.');

    var record = found.data;
    // Sólo estos campos son editables. El id NUNCA cambia: es lo que está
    // impreso en el QR físico.
    if (body.nombre !== undefined) record.nombre = String(body.nombre);
    if (body.descripcion !== undefined) record.descripcion = String(body.descripcion);
    if (body.design_json !== undefined) record.design_json = String(body.design_json);
    if (body.activo !== undefined) record.activo = normalizeBool_(body.activo, true);
    if (body.url_destino !== undefined) {
      record.url_destino = record.dinamico
        ? assertSafeUrl_(body.url_destino)
        : String(body.url_destino);
    }
    record.fecha_actualizacion = nowParts_().iso;

    var row = QR_HEADERS.map(function (h) { return record[h]; });
    found.sheet.getRange(found.rowNumber, 1, 1, QR_HEADERS.length).setValues([row]);
    return record;
  } finally {
    lock.releaseLock();
  }
}

function apiListScans_(body) {
  var sheet = openSheet_(SHEET_SCANS, SCAN_HEADERS);
  var values = sheet.getDataRange().getValues();
  var out = [];
  var filter = body && body.qr_id ? String(body.qr_id).toUpperCase() : null;
  for (var i = 1; i < values.length; i++) {
    var obj = rowToObject_(SCAN_HEADERS, values[i]);
    if (filter && String(obj.qr_id).toUpperCase() !== filter) continue;
    out.push(obj);
  }
  return out.slice(-500);
}

// ------------------------------------------------------------- redirección
function handleRedirect_(qrId, e) {
  var found;
  try {
    found = findRow_(qrId);
  } catch (err) {
    // Nunca exponemos detalles de la hoja al público (sección 6 del spec).
    return errorPage_('No fue posible procesar este código.');
  }

  if (!found) return errorPage_('QR no encontrado');
  if (!found.data.activo) return errorPage_('Este QR está temporalmente inactivo.');
  if (!found.data.dinamico) return errorPage_('Este código no es de redirección.');

  var destino = String(found.data.url_destino || '');
  if (!/^https?:\/\//i.test(destino)) {
    return errorPage_('Este QR no tiene un destino válido configurado.');
  }

  logScan_(found.data.id, e);
  return redirectPage_(destino);
}

function logScan_(qrId, e) {
  // El registro no debe poder romper la redirección: si falla, seguimos.
  try {
    var sheet = openSheet_(SHEET_SCANS, SCAN_HEADERS);
    var t = nowParts_();
    var params = (e && e.parameter) ? e.parameter : {};
    // Apps Script no expone la IP ni el User-Agent del visitante: esas dos
    // columnas quedan vacías a propósito (ver README, "Limitaciones").
    sheet.appendRow([
      Utilities.getUuid().slice(0, 8),
      qrId,
      t.fecha,
      t.hora,
      '',
      '',
      String(params.ref || '')
    ]);
  } catch (err) {
    console.warn('No se pudo registrar el escaneo: ' + err);
  }
}

function redirectPage_(url) {
  // Apps Script NO puede emitir un 302 real: una Web App sólo devuelve
  // contenido. Esta página hace el salto por JavaScript con meta-refresh
  // de respaldo — funciona en todos los lectores de QR modernos.
  var safe = url.replace(/"/g, '&quot;').replace(/</g, '&lt;');
  var html =
    '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<meta http-equiv="refresh" content="0;url=' + safe + '">' +
    '<title>Redirigiendo…</title>' +
    '<style>body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;' +
    'display:flex;align-items:center;justify-content:center;height:100vh;margin:0;' +
    'color:#0F172A;background:#F8FAFC}</style></head><body>' +
    '<p>Redirigiendo… <a href="' + safe + '">Continuar</a></p>' +
    '<script>window.location.replace("' + safe.replace(/"/g, '\\"') + '");<\/script>' +
    '</body></html>';
  return HtmlService.createHtmlOutput(html)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function errorPage_(message) {
  var safe = String(message).replace(/</g, '&lt;');
  var html =
    '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>IntelliQR</title>' +
    '<style>body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;' +
    'display:flex;align-items:center;justify-content:center;height:100vh;margin:0;' +
    'background:#F8FAFC;color:#0F172A;text-align:center;padding:24px}' +
    'h1{font-size:20px;margin:0 0 8px}p{color:#64748B;margin:0}</style></head><body>' +
    '<div><h1>' + safe + '</h1><p>IntelliQR</p></div></body></html>';
  return HtmlService.createHtmlOutput(html)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ------------------------------------------------------- inicialización manual
/**
 * Ejecuta esta función UNA VEZ desde el editor de Apps Script (botón
 * "Ejecutar") para crear las tres hojas con sus encabezados.
 */
function setupSheets() {
  openSheet_(SHEET_QR, QR_HEADERS);
  openSheet_(SHEET_USERS, USER_HEADERS);
  openSheet_(SHEET_SCANS, SCAN_HEADERS);
  Logger.log('Hojas creadas o verificadas correctamente.');
}
