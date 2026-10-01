"""
Orquesta el flujo completo de creación de QR (sección 7 del spec):
1. Contenido  2. Diseño  3. Exportar
Con un indicador de progreso elegante en la parte superior.
"""
from __future__ import annotations
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget, QFrame
from PySide6.QtCore import Qt, Signal

from ui.qr.qr_type_selector import QRTypeSelector
from ui.qr.qr_content import QRContentStep
from ui.qr.qr_design import QRDesignStep
from ui.qr.qr_export import QRExportStep
from core.qr_engine.generator import QRGenerator, QRDesignOptions
from core.qr_engine.designer import FrameOptions, apply_frame
from database.repositories.qr_repository import QRRepository
from ui import theme
from ui.i18n import tr

_STEP_KEYS = ["qrwizard.step.content", "qrwizard.step.design", "qrwizard.step.export"]


class _StepIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StepIndicator")
        self._layout = QHBoxLayout(self)
        self._labels: list[QLabel] = []
        self._active_index = 0
        for _ in _STEP_KEYS:
            label = QLabel()
            self._labels.append(label)
            self._layout.addWidget(label)
        self._layout.addStretch()
        self.retranslate()
        self.set_active(0)

    def retranslate(self) -> None:
        for label, key in zip(self._labels, _STEP_KEYS):
            label.setText(tr(key))
        self.set_active(self._active_index)

    def set_active(self, index: int) -> None:
        self._active_index = index
        for i, label in enumerate(self._labels):
            if i == index:
                label.setStyleSheet(
                    f"color: {theme.PRIMARY}; font-weight: 700; padding: 6px 14px; "
                    f"border-bottom: 3px solid {theme.PRIMARY};"
                )
            elif i < index:
                label.setStyleSheet(f"color: {theme.SUCCESS}; font-weight: 600; padding: 6px 14px;")
            else:
                label.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-weight: 600; padding: 6px 14px;")


class QRWizard(QWidget):
    """Widget de página completa embebido en el área de contenido de la ventana principal."""

    completed = Signal()  # el usuario pulsó "Listo" y terminó el flujo

    def __init__(self, parent=None):
        super().__init__(parent)
        self._generator = QRGenerator()
        self._repo = QRRepository()

        # estado del flujo
        self._type_id: str | None = None
        self._content_data: dict = {}
        self._payload: str = ""
        self._design_data: dict = {}
        self._frame_data: dict = {}
        self._final_image = None
        self._editing_qr_id: int | None = None

        root = QVBoxLayout(self)

        self.step_indicator = _StepIndicator()
        self.step_indicator.hide()
        root.addWidget(self.step_indicator)

        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self.type_selector = QRTypeSelector()
        self.content_step = QRContentStep()
        self.design_step = QRDesignStep()
        self.export_step = QRExportStep()

        self.stack.addWidget(self.type_selector)   # 0
        self.stack.addWidget(self.content_step)     # 1
        self.stack.addWidget(self.design_step)       # 2
        self.stack.addWidget(self.export_step)        # 3

        self.type_selector.type_chosen.connect(self._on_type_chosen)
        self.content_step.content_ready.connect(self._on_content_ready)
        self.content_step.back_requested.connect(self._go_to_type_selector)
        self.design_step.design_ready.connect(self._on_design_ready)
        self.design_step.back_requested.connect(lambda: self._go_to(1))
        self.export_step.back_requested.connect(lambda: self._go_to(2))
        self.export_step.save_project_requested.connect(self._on_save_project)
        self.export_step.finished.connect(self._on_finished)

        self.reset()

    def _on_finished(self) -> None:
        """Al terminar, limpiamos el asistente y avisamos a la ventana para
        que lleve al usuario a 'Mis QR' en vez de dejarlo en una pantalla
        en blanco."""
        self.reset()
        self.completed.emit()

    def reset(self) -> None:
        self._type_id = None
        self._content_data = {}
        self._payload = ""
        self._design_data = {}
        self._frame_data = {}
        self._final_image = None
        self._editing_qr_id = None
        self.step_indicator.hide()
        self.stack.setCurrentIndex(0)

    def retranslate(self) -> None:
        self.step_indicator.retranslate()
        self.type_selector.retranslate()
        self.content_step.retranslate()
        self.design_step.retranslate()
        self.export_step.retranslate()

    def _go_to(self, index: int) -> None:
        self.step_indicator.set_active(max(index - 1, 0))
        self.stack.setCurrentIndex(index)

    def _go_to_type_selector(self) -> None:
        self.step_indicator.hide()
        self.stack.setCurrentIndex(0)

    def _on_type_chosen(self, type_id: str) -> None:
        self._type_id = type_id
        self.content_step.load_type(type_id)
        self.step_indicator.show()
        self._go_to(1)

    def _on_content_ready(self, type_id: str, data: dict, payload: str) -> None:
        self._type_id = type_id
        self._content_data = data
        self._payload = payload
        self.design_step.load_payload(payload)
        self._go_to(2)

    def _on_design_ready(self, design_data: dict, frame_data: dict) -> None:
        self._design_data = design_data
        self._frame_data = frame_data
        design_options = QRDesignOptions(**design_data)
        result = self._generator.generate(self._payload, design_options)
        frame_options = FrameOptions(
            style=frame_data["style"],
            text=frame_data["text"],
            frame_color=frame_data.get("frame_color", "#2563EB"),
            text_color=frame_data.get("frame_text_color", "#FFFFFF"),
        )
        self._final_image = apply_frame(result.image, frame_options)
        self.export_step.load_result(self._final_image, self._payload)
        self._go_to(3)

    def _on_save_project(self, name: str) -> None:
        new_id = self._repo.save(
            name=name,
            type_id=self._type_id or "text",
            payload=self._payload,
            content_data=self._content_data,
            design_data={
                **self._design_data,
                "frame_style": self._frame_data.get("style", "ninguno"),
                "frame_text": self._frame_data.get("text", "ESCANÉAME"),
                "frame_color": self._frame_data.get("frame_color", "#2563EB"),
                "frame_text_color": self._frame_data.get("frame_text_color", "#FFFFFF"),
            },
            qr_id=self._editing_qr_id,
        )
        self._editing_qr_id = new_id

    def open_existing(self, qr_id: int) -> None:
        """Carga un QR ya guardado (desde 'Mis QR' o 'Recientes') y lo muestra
        directamente en el paso de exportación, permitiendo volver atrás para
        editar contenido o diseño sin perder lo ya guardado."""
        record = self._repo.get(qr_id)
        if record is None:
            return

        self._editing_qr_id = record.id
        self._type_id = record.type_id
        self._content_data = json.loads(record.content_data_json) if record.content_data_json else {}
        self._payload = record.payload

        design = record.design
        if design is not None:
            self._design_data = {
                "pattern": design.pattern,
                "corner_style": design.corner_style,
                "fg_color": design.fg_color,
                "bg_color": design.bg_color,
                "gradient_enabled": design.gradient_enabled,
                "gradient_start": design.gradient_start,
                "gradient_end": design.gradient_end,
                "gradient_direction": "horizontal",
                "logo_path": design.logo_path,
                "logo_size_ratio": design.logo_size_ratio,
                "transparent_background": design.transparent_background,
                "box_size": design.box_size,
            }
            self._frame_data = {
                "style": design.frame_style,
                "text": design.frame_text,
                "frame_color": design.frame_color,
                "frame_text_color": design.frame_text_color,
            }
        else:
            self._design_data = {}
            self._frame_data = {"style": "ninguno", "text": "ESCANÉAME"}

        self.content_step.load_type(self._type_id, self._content_data)
        self.design_step.load_payload(self._payload, previous_design=self._design_data)

        design_options = QRDesignOptions(**self._design_data) if self._design_data else QRDesignOptions()
        result = self._generator.generate(self._payload, design_options)
        frame_options = FrameOptions(
            style=self._frame_data.get("style", "ninguno"),
            text=self._frame_data.get("text", "ESCANÉAME"),
            frame_color=self._frame_data.get("frame_color", "#2563EB"),
            text_color=self._frame_data.get("frame_text_color", "#FFFFFF"),
        )
        self._final_image = apply_frame(result.image, frame_options)
        self.export_step.load_result(self._final_image, self._payload)
        self.export_step.project_name_input.setText(record.name)
        self.export_step.mark_saved()

        self.step_indicator.show()
        self._go_to(3)
