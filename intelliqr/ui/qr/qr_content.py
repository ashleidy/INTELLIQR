"""Paso 1 del flujo de creación de QR: contenido (sección 10-12 del spec)."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Signal, QTimer

from qr_types.registry import get_type
from core.qr_engine.generator import QRGenerator, QRDesignOptions
from core.qr_engine.validator import check_payload_size
from ui.qr.form_schemas import FORM_SCHEMAS
from ui.qr.qr_preview import QRPreviewWidget
from ui.i18n import tr


class QRContentStep(QWidget):
    """Emite `content_ready(type_id, data, payload)` cuando el contenido es válido
    y el usuario pulsa Continuar."""
    content_ready = Signal(str, dict, str)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._type_id: str | None = None
        self._fields: dict[str, QWidget] = {}
        self._error_labels: dict[str, QLabel] = {}
        self._generator = QRGenerator()

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(200)
        self._debounce.timeout.connect(self._update_preview)

        root = QHBoxLayout(self)

        # --- Columna izquierda: formulario ---
        left = QVBoxLayout()
        self.title_label = QLabel(tr("qrcontent.title"))
        self.title_label.setObjectName("H2")
        left.addWidget(self.title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.addStretch()
        scroll.setWidget(self.form_container)
        left.addWidget(scroll, 1)

        nav_row = QHBoxLayout()
        self.back_btn = QPushButton(tr("qrcontent.back"))
        self.back_btn.setObjectName("SecondaryButton")
        self.back_btn.clicked.connect(self.back_requested.emit)
        self.continue_btn = QPushButton(tr("qrcontent.continue"))
        self.continue_btn.setObjectName("PrimaryButton")
        self.continue_btn.clicked.connect(self._on_continue)
        nav_row.addWidget(self.back_btn)
        nav_row.addStretch()
        nav_row.addWidget(self.continue_btn)
        left.addLayout(nav_row)

        # --- Columna derecha: preview ---
        right = QVBoxLayout()
        self.preview = QRPreviewWidget()
        right.addWidget(self.preview)
        right.addStretch()

        root.addLayout(left, 3)
        root.addLayout(right, 2)

    def load_type(self, type_id: str, initial_data: dict | None = None) -> None:
        """Reconstruye el formulario para el tipo de QR seleccionado."""
        self._type_id = type_id
        qr_type = get_type(type_id)
        self.title_label.setText(f"{tr('qrcontent.title')} · {tr(f'qrtype.{type_id}.name')}")

        # limpiar formulario anterior
        while self.form_layout.count() > 1:
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._fields.clear()
        self._error_labels.clear()

        schema = FORM_SCHEMAS.get(type_id, [])
        initial_data = initial_data or {}
        for f in schema:
            label = QLabel(f.label)
            self.form_layout.insertWidget(self.form_layout.count() - 1, label)

            widget: QWidget
            if f.kind == "textarea":
                widget = QTextEdit()
                widget.setPlaceholderText(f.placeholder)
                widget.setFixedHeight(80)
                widget.setPlainText(str(initial_data.get(f.key, f.default)))
                widget.textChanged.connect(self._on_field_changed)
            elif f.kind == "select":
                widget = QComboBox()
                widget.addItems(f.options)
                current = initial_data.get(f.key, f.default)
                if current in f.options:
                    widget.setCurrentText(current)
                widget.currentTextChanged.connect(self._on_field_changed)
            elif f.kind == "checkbox":
                widget = QCheckBox()
                widget.setChecked(bool(initial_data.get(f.key, f.default)))
                widget.stateChanged.connect(self._on_field_changed)
            else:
                widget = QLineEdit()
                widget.setPlaceholderText(f.placeholder)
                widget.setText(str(initial_data.get(f.key, f.default)))
                widget.textChanged.connect(self._on_field_changed)

            self._fields[f.key] = widget
            self.form_layout.insertWidget(self.form_layout.count() - 1, widget)

            error_label = QLabel("")
            error_label.setObjectName("ErrorLabel")
            error_label.hide()
            self._error_labels[f.key] = error_label
            self.form_layout.insertWidget(self.form_layout.count() - 1, error_label)

        self._update_preview()

    def _collect_data(self) -> dict:
        data = {}
        for key, widget in self._fields.items():
            if isinstance(widget, QLineEdit):
                data[key] = widget.text()
            elif isinstance(widget, QTextEdit):
                data[key] = widget.toPlainText()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                data[key] = widget.isChecked()
        return data

    def _on_field_changed(self, *args) -> None:
        for label in self._error_labels.values():
            label.hide()
        self._debounce.start()

    def _update_preview(self) -> None:
        if not self._type_id:
            return
        qr_type = get_type(self._type_id)
        data = self._collect_data()
        result = qr_type.validate(data)
        if not result.is_valid:
            self.preview.show_placeholder("Completa el contenido para ver la vista previa.")
            return
        try:
            payload = qr_type.build_payload(data)
        except Exception:
            self.preview.show_placeholder(tr("qrcontent.error_generic"))
            return
        size_error = check_payload_size(payload)
        if size_error:
            self.preview.show_placeholder(size_error)
            return
        try:
            gen_result = self._generator.generate(payload, QRDesignOptions())
            self.preview.show_image(gen_result.image, gen_result.warnings)
        except Exception:
            self.preview.show_placeholder(tr("qrcontent.error_generic"))

    def _on_continue(self) -> None:
        if not self._type_id:
            return
        qr_type = get_type(self._type_id)
        data = self._collect_data()
        result = qr_type.validate(data)
        for key, label in self._error_labels.items():
            label.hide()
        if not result.is_valid:
            for field_key, message in result.errors.items():
                if field_key in self._error_labels:
                    self._error_labels[field_key].setText(message)
                    self._error_labels[field_key].show()
            return
        payload = qr_type.build_payload(data)
        self.content_ready.emit(self._type_id, data, payload)

    def retranslate(self) -> None:
        """Actualiza los textos fijos (botones, título) al idioma actual."""
        self.back_btn.setText(tr("qrcontent.back"))
        self.continue_btn.setText(tr("qrcontent.continue"))
        if self._type_id:
            self.title_label.setText(f"{tr('qrcontent.title')} · {tr(f'qrtype.{self._type_id}.name')}")
        else:
            self.title_label.setText(tr("qrcontent.title"))
