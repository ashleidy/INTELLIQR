from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
    QFileDialog, QMessageBox, QScrollArea, QApplication
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QImage, QPixmap, QDesktopServices
from PySide6.QtCore import Signal
from PIL import Image

from core.scan_engine.scanner import Scanner, ScanResult, classify_action
from database.repositories.scan_repository import ScanRepository
from ui.common.image_viewer import show_image_viewer, save_image_with_dialog
from ui import theme
from ui.i18n import tr


try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


_SUPPORTED_2D = [
    ("scanner.supported.qr",         "QR Code"),
    ("scanner.supported.datamatrix", "Data Matrix"),
    ("scanner.supported.aztec",      "Aztec"),
    ("scanner.supported.pdf417",     "PDF417"),
    ("scanner.supported.microqr",    "MicroQR"),
]
_SUPPORTED_1D = [
    ("scanner.supported.ean_upc",         "EAN-13 · EAN-8 · UPC-A · UPC-E"),
    ("scanner.supported.code128_39_93",   "Code 128 · Code 39 · Code 93"),
    ("scanner.supported.itf_codabar_gs1", "ITF · Codabar · GS1-128"),
]

_TYPE_LABEL_KEYS = {
    "codigo qr": "scanner.type.qr",
    "qr code": "scanner.type.qr",
    "qr": "scanner.type.qr",
    "codigo de barras": "scanner.type.barcode",
    "barcode": "scanner.type.barcode",
    "data matrix": "scanner.type.datamatrix",
    "datamatrix": "scanner.type.datamatrix",
    "aztec": "scanner.type.aztec",
    "pdf417": "scanner.type.pdf417",
    "microqr": "scanner.type.microqr",
}


def _tr_with_fallback(key: str, fallback: str) -> str:
    value = tr(key)
    return fallback if (not value or value == key) else value


def _normalize(text: str) -> str:
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    ).strip()


def _translate_type_label(raw: str) -> str:
    key = _TYPE_LABEL_KEYS.get(_normalize(raw))
    if key is None:
        return raw
    return _tr_with_fallback(key, raw)


def _pil_to_qpixmap(image: Image.Image) -> QPixmap:
    """PIL.Image -> QPixmap. Necesario para mostrar el QR capturado."""
    if image.mode != "RGB":
        image = image.convert("RGB")
    data = image.tobytes("raw", "RGB")
    qimg = QImage(data, image.width, image.height, image.width * 3, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


def _captured_image(source: Image.Image) -> Image.Image:
    """Devuelve la imagen tal como se escaneó (el frame completo de la
    cámara, o la imagen cargada), sin recortar.

    Antes se recortaba ajustado a la bounding box de los módulos del QR
    (con apenas 10px de margen), así que cualquier marco/etiqueta de diseño
    alrededor del código (p. ej. "ESCANÉAME") quedaba fuera de lo guardado
    y de lo mostrado en Resultado/Historial: lo guardado no coincidía con
    lo que realmente se había escaneado."""
    return source.copy()


class _ResultRow(QFrame):
    """Fila de resultado: muestra el QR capturado + acciones
    Copy · Open · Save · Erase. Guarda el PIL image recortado para que
    `_on_save_result` lo persista en el historial."""

    def __init__(self, result: ScanResult, qr_image: Image.Image,
                 on_save, on_erase, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._result = result
        self._qr_image = qr_image            # PIL.Image listo para guardar
        self._openable_url = classify_action(result.content)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(12)

        # --- Miniatura del QR capturado (esto es lo que faltaba) ---------
        self.thumb = QLabel()
        self.thumb.setFixedSize(96, 96)
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setStyleSheet(
            "background-color: #F1F5F9; border-radius: 8px;"
        )
        if self._qr_image is not None:
            self.thumb.setPixmap(
                _pil_to_qpixmap(self._qr_image).scaled(
                    92, 92, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
            self.thumb.setCursor(Qt.PointingHandCursor)
            self.thumb.mousePressEvent = lambda _e: self._on_view()
        outer.addWidget(self.thumb)

        # --- Columna con textos + botones --------------------------------
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(6)

        self.type_label = QLabel()
        self.type_label.setObjectName("H3")
        self.content_label = QLabel(result.content)
        self.content_label.setWordWrap(True)
        col.addWidget(self.type_label)
        col.addWidget(self.content_label)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(6)

        self.copy_btn = QPushButton()
        self.copy_btn.setObjectName("SecondaryButton")
        self.copy_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(self._result.content)
        )
        buttons_row.addWidget(self.copy_btn)

        self.open_btn = QPushButton()
        self.open_btn.setObjectName("SecondaryButton")
        if self._openable_url:
            self.open_btn.clicked.connect(self._on_open)
        else:
            self.open_btn.setEnabled(False)
        buttons_row.addWidget(self.open_btn)

        self.view_btn = QPushButton()
        self.view_btn.setObjectName("SecondaryButton")
        self.download_btn = QPushButton()
        self.download_btn.setObjectName("SecondaryButton")
        if self._qr_image is not None:
            self.view_btn.clicked.connect(self._on_view)
            self.download_btn.clicked.connect(self._on_download)
        else:
            self.view_btn.setEnabled(False)
            self.download_btn.setEnabled(False)
        buttons_row.addWidget(self.view_btn)
        buttons_row.addWidget(self.download_btn)

        self.save_btn = QPushButton()
        self.save_btn.setObjectName("PrimaryButton")
        self.save_btn.clicked.connect(lambda: on_save(self._result, self._qr_image))
        buttons_row.addWidget(self.save_btn)

        self.erase_btn = QPushButton()
        self.erase_btn.setObjectName("SecondaryButton")
        self.erase_btn.clicked.connect(lambda: on_erase(self))
        buttons_row.addWidget(self.erase_btn)

        buttons_row.addStretch()
        col.addLayout(buttons_row)
        outer.addLayout(col, 1)

        self.retranslate()

    def _on_open(self) -> None:
        # Mismo patrón de aviso que usa el código de barras al exportar:
        # si falla, se muestra un QMessageBox en vez de fallar en silencio.
        try:
            opened = QDesktopServices.openUrl(QUrl(self._openable_url))
        except Exception:
            opened = False
        if not opened:
            QMessageBox.warning(self, tr("scanner.open_fail_title"), tr("scanner.open_fail_msg"))

    def _on_view(self) -> None:
        if self._qr_image is None:
            return
        show_image_viewer(self, self._qr_image, suggested_name=self._result.type_label)

    def _on_download(self) -> None:
        if self._qr_image is None:
            return
        save_image_with_dialog(self, self._qr_image, suggested_name=self._result.type_label)

    def retranslate(self) -> None:
        self.type_label.setText(_translate_type_label(self._result.type_label))
        self.copy_btn.setText(tr("scanner.copy"))
        self.open_btn.setText(tr("scanner.open"))
        self.view_btn.setText(tr("scanhistory.view"))
        self.download_btn.setText(tr("scanhistory.download"))
        self.save_btn.setText(tr("scanner.save"))
        self.erase_btn.setText(tr("scanner.erase"))
        self.open_btn.setToolTip(
            "" if self._openable_url else tr("scanner.open_unavailable_tip")
        )
        no_image_tip = tr("scanhistory.no_image_tip")
        self.view_btn.setToolTip("" if self._qr_image is not None else no_image_tip)
        self.download_btn.setToolTip("" if self._qr_image is not None else no_image_tip)


class ScannerScreen(QWidget):
    scan_saved = Signal() 
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scanner = Scanner()
        self._repo = ScanRepository()
        self._capture = None
        self._last_contents_shown: set[str] = set()

        self._camera_timer = QTimer(self)
        self._camera_timer.setInterval(60)
        self._camera_timer.timeout.connect(self._on_camera_frame)

        root = QHBoxLayout(self)
        left = QVBoxLayout()

        self.title_label = QLabel()
        self.title_label.setObjectName("H1")
        left.addWidget(self.title_label)
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("Subtitle")
        self.subtitle_label.setWordWrap(True)
        left.addWidget(self.subtitle_label)

        self.supported_card = QFrame()
        self.supported_card.setObjectName("Card")
        supported_layout = QVBoxLayout(self.supported_card)
        supported_layout.setContentsMargins(20, 16, 20, 16)
        supported_layout.setSpacing(10)

        self.supported_title = QLabel()
        self.supported_title.setObjectName("H3")
        supported_layout.addWidget(self.supported_title)

        self._chips_2d_row = self._make_chip_row()
        self._chips_1d_row = self._make_chip_row()
        supported_layout.addLayout(self._chips_2d_row)
        supported_layout.addLayout(self._chips_1d_row)

        left.addWidget(self.supported_card)

        self.video_label = QLabel()
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setMaximumSize(480, 360)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet(
            "background-color: #000; border-radius: 8px; color: white;"
        )
        self.video_label.setText(tr("scanner.camera_stopped"))
        left.addWidget(self.video_label)

        buttons_row = QHBoxLayout()
        self.start_btn = QPushButton()
        self.start_btn.setObjectName("PrimaryButton")
        self.start_btn.clicked.connect(self._start_camera)
        self.stop_btn = QPushButton()
        self.stop_btn.setObjectName("SecondaryButton")
        self.stop_btn.clicked.connect(self._stop_camera)
        self.stop_btn.setEnabled(False)
        load_btn = QPushButton()
        self.load_btn = load_btn
        load_btn.setObjectName("SecondaryButton")
        load_btn.clicked.connect(self._on_load_image)
        buttons_row.addWidget(self.start_btn)
        buttons_row.addWidget(self.stop_btn)
        buttons_row.addWidget(load_btn)
        left.addLayout(buttons_row)

        left.addStretch()

        right = QVBoxLayout()
        self.results_label = QLabel()
        right.addWidget(self.results_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.addStretch()
        scroll.setWidget(self.results_container)
        right.addWidget(scroll)

        root.addLayout(left, 3)
        root.addLayout(right, 2)

        self.retranslate()

    # ---------- Chips ----------
    def _make_chip_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addStretch()
        return row

    def _fill_chip_row(self, layout: QHBoxLayout, items: list[tuple[str, str]]) -> None:
        while layout.count() > 1:
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for idx, (key, fallback) in enumerate(items):
            chip = QLabel(_tr_with_fallback(key, fallback))
            chip.setStyleSheet(
                "background-color: #E8EEFB;"
                " color: #2563EB;"
                " border-radius: 10px;"
                " padding: 4px 10px;"
                " font-size: 12px;"
                " font-weight: 600;"
            )
            layout.insertWidget(idx, chip)

    def _rebuild_supported_list(self) -> None:
        self._fill_chip_row(self._chips_2d_row, _SUPPORTED_2D)
        self._fill_chip_row(self._chips_1d_row, _SUPPORTED_1D)

    # ---------- Cámara ----------
    def _start_camera(self) -> None:
        if not _CV2_AVAILABLE:
            QMessageBox.warning(self, tr("scanner.camera_unavailable_title"),
                                 tr("scanner.camera_unavailable_msg"))
            return
        self._capture = cv2.VideoCapture(0)
        if not self._capture.isOpened():
            QMessageBox.warning(self, tr("scanner.camera_unavailable_title"),
                                 tr("scanner.camera_open_fail_msg"))
            self._capture = None
            return
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._last_contents_shown.clear()
        self._camera_timer.start()

    def _stop_camera(self) -> None:
        self._camera_timer.stop()
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.video_label.clear()
        self.video_label.setText(tr("scanner.camera_stopped"))

    def _on_camera_frame(self) -> None:
        if self._capture is None:
            return
        ok, frame = self._capture.read()
        if not ok:
            return

        # Guardamos también la versión PIL (es la fuente para recortar el QR).
        pil_source = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        results = self._scanner.decode(pil_source)

        for result in results:
            x, y, w, h = result.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (37, 99, 235), 3)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb_frame.shape
        qimage = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        self.video_label.setPixmap(pixmap)

        for result in results:
            if result.content not in self._last_contents_shown:
                self._last_contents_shown.add(result.content)
                qr_img = _captured_image(pil_source)
                self._add_result(result, qr_img)

    # ---------- Cargar imagen ----------
    def _on_load_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("scanner.load_image_dialog"), "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp)",
        )
        if not path:
            return
        try:
            image = Image.open(path)
        except Exception:
            QMessageBox.warning(self, tr("scanner.image_open_fail_title"),
                                 tr("scanner.image_open_fail_msg"))
            return

        results = self._scanner.decode(image)
        if not results:
            QMessageBox.information(self, tr("scanner.no_results_title"),
                                     tr("scanner.no_results_msg"))
            return

        pixmap = QPixmap(path).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        self.video_label.setPixmap(pixmap)

        for result in results:
            qr_img = _captured_image(image)
            self._add_result(result, qr_img)

    # ---------- Resultados ----------
    def _add_result(self, result: ScanResult, qr_image: Image.Image) -> None:
        row = _ResultRow(
            result,
            qr_image,
            on_save=self._on_save_result,
            on_erase=self._on_erase_result,
        )
        self.results_layout.insertWidget(0, row)

    def _on_save_result(self, result: ScanResult, qr_image: Image.Image) -> None:
        
        try:
            self._repo.save(result.type_label, result.content, image=qr_image)
        except TypeError:
            # Repo antiguo: guardamos solo texto, pero avisamos.
            self._repo.save(result.type_label, result.content)
        self.scan_saved.emit()
        QMessageBox.information(self, tr("scanner.save_done_title"),
                                 tr("scanner.save_done_msg"))

    def _on_erase_result(self, row: _ResultRow) -> None:
        self._last_contents_shown.discard(row._result.content)
        self.results_layout.removeWidget(row)
        row.deleteLater()

    # ---------- Ciclo de vida ----------
    def closeEvent(self, event) -> None:
        self._stop_camera()
        super().closeEvent(event)

    def hideEvent(self, event) -> None:
        self._stop_camera()
        super().hideEvent(event)

    # ---------- Traducción ----------
    def retranslate(self) -> None:
        self.title_label.setText(tr("scanner.title"))
        self.subtitle_label.setText(tr("scanner.subtitle"))
        self.start_btn.setText(tr("scanner.start_camera"))
        self.stop_btn.setText(tr("scanner.stop_camera"))
        self.load_btn.setText(tr("scanner.load_image"))
        self.results_label.setText(tr("scanner.results"))
        self.supported_title.setText(
            _tr_with_fallback("scanner.supported_title", "Qué puede escanear")
        )
        self._rebuild_supported_list()
        if self._capture is None:
            self.video_label.setText(tr("scanner.camera_stopped"))

        # Retraducir todas las filas ya creadas
        for row in self.findChildren(_ResultRow):
            row.retranslate()