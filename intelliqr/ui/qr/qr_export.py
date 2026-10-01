
from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QFileDialog, QLineEdit, QMessageBox
)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QPainter
from PySide6.QtCore import Signal

from datetime import datetime

from core.qr_engine.exporter import QRExporter, ExportOptions, resolve_size_cm
from ui.qr.qr_preview import QRPreviewWidget, pil_to_qimage
from app.config import EXPORTS_DIR
from ui.i18n import tr


class QRExportStep(QWidget):
    back_requested = Signal()
    save_project_requested = Signal(str)  # nombre del proyecto
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._final_image = None
        self._payload = ""
        self._exporter = QRExporter()
        self._saved = False  # ¿el QR actual ya está guardado en "Mis QR"?

        root = QHBoxLayout(self)
        left = QVBoxLayout()

        self.title_label = QLabel()
        self.title_label.setObjectName("H2")
        left.addWidget(self.title_label)

        self.format_label = QLabel()
        left.addWidget(self.format_label)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "SVG", "PDF"])
        left.addWidget(self.format_combo)

        self.resolution_label = QLabel()
        left.addWidget(self.resolution_label)
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["300 DPI", "600 DPI"])
        left.addWidget(self.dpi_combo)

        self.size_label = QLabel()
        left.addWidget(self.size_label)
        self.size_combo = QComboBox()
        self.size_combo.addItems(["Original", "Pequeño (3x3 cm)", "Mediano (5x5 cm)", "Grande (10x10 cm)", "Personalizado"])
        left.addWidget(self.size_combo)

        custom_row = QHBoxLayout()
        self.custom_w = QLineEdit()
        self.custom_w.setPlaceholderText("Ancho (cm)")
        self.custom_h = QLineEdit()
        self.custom_h.setPlaceholderText("Alto (cm)")
        custom_row.addWidget(self.custom_w)
        custom_row.addWidget(self.custom_h)
        left.addLayout(custom_row)

        export_row = QHBoxLayout()
        self.export_btn = QPushButton()
        self.export_btn.setObjectName("PrimaryButton")
        self.export_btn.clicked.connect(self._on_export)
        self.print_btn = QPushButton()
        self.print_btn.setObjectName("SecondaryButton")
        self.print_btn.clicked.connect(self._on_print)
        export_row.addWidget(self.export_btn)
        export_row.addWidget(self.print_btn)
        left.addLayout(export_row)

        self.save_project_label = QLabel()
        left.addWidget(self.save_project_label)
        save_row = QHBoxLayout()
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("nombre_del_proyecto")
        save_btn = QPushButton()
        self.save_btn = save_btn
        save_btn.setObjectName("SecondaryButton")
        save_btn.clicked.connect(self._on_save_project)
        save_row.addWidget(self.project_name_input)
        save_row.addWidget(save_btn)
        left.addLayout(save_row)

        nav_row = QHBoxLayout()
        self.back_btn = QPushButton()
        self.back_btn.setObjectName("SecondaryButton")
        self.back_btn.clicked.connect(self.back_requested.emit)
        self.done_btn = QPushButton()
        self.done_btn.setObjectName("PrimaryButton")
        self.done_btn.clicked.connect(self._on_done)
        nav_row.addWidget(self.back_btn)
        nav_row.addStretch()
        nav_row.addWidget(self.done_btn)
        left.addLayout(nav_row)
        left.addStretch()

        right = QVBoxLayout()
        self.preview = QRPreviewWidget()
        right.addWidget(self.preview, 1)

        root.addLayout(left, 2)
        root.addLayout(right, 3)

        self.retranslate()

    def load_result(self, final_image, payload: str) -> None:
        self._final_image = final_image
        self._payload = payload
        self._saved = False
        self.preview.show_image(final_image)

    def mark_saved(self) -> None:
        """La ventana llama a esto cuando el QR ya está guardado (p. ej. al
        abrir uno existente desde 'Mis QR')."""
        self._saved = True

    def _build_export_options(self) -> ExportOptions:
        fmt = self.format_combo.currentText()
        dpi = 600 if "600" in self.dpi_combo.currentText() else 300
        size_label_map = {
            "Original": None, "Pequeño (3x3 cm)": "Pequeño",
            "Mediano (5x5 cm)": "Mediano", "Grande (10x10 cm)": "Grande",
            "Personalizado": "Personalizado",
        }
        size_choice = size_label_map.get(self.size_combo.currentText())
        size_cm = None
        if size_choice:
            try:
                custom_w = float(self.custom_w.text()) if self.custom_w.text() else None
                custom_h = float(self.custom_h.text()) if self.custom_h.text() else None
            except ValueError:
                custom_w = custom_h = None
            size_cm = resolve_size_cm(size_choice, custom_w, custom_h)

        # NUEVO: nombre del proyecto (si el usuario lo asignó) manda.
        project_name = self.project_name_input.text().strip() or None

        return ExportOptions(fmt=fmt, dpi=dpi, size_cm=size_cm, name=project_name)

    def _on_export(self) -> None:
        if self._final_image is None:
            return

        options = self._build_export_options()
        ext_map = {"PNG": "png", "JPG": "jpg", "SVG": "svg", "PDF": "pdf"}
        ext = ext_map[options.fmt]

        # NUEVO: si hay nombre de proyecto, se usa como nombre por defecto del diálogo.
        file_stem = options.name or "qr_export"
        default_path = str(EXPORTS_DIR / f"{file_stem}.{ext}")

        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("qrexport.export_dialog_title"),   # opcional, ver nota abajo
            default_path,
            f"Archivos {options.fmt} (*.{ext})",
        )
        if not path:
            return

        try:
            self._exporter.export(self._final_image, Path(path), options, payload=self._payload)
            QMessageBox.information(self, tr("qrexport.export_done_title"),
                                    tr("qrexport.export_done_msg"))
        except Exception:
            QMessageBox.warning(self, tr("qrexport.export_fail_title"),
                                tr("qrexport.export_fail_msg"))

    def _on_print(self) -> None:
        if self._final_image is None:
            return
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.Accepted:
            return
        painter = QPainter(printer)
        qimage = pil_to_qimage(self._final_image)
        rect = painter.viewport()
        scaled = qimage.scaled(rect.size().boundedTo(qimage.size()))
        painter.drawImage(0, 0, scaled)
        painter.end()

    def _default_project_name(self) -> str:
        return f"qr_{datetime.now():%Y%m%d_%H%M}"

    def _save_project(self, name: str) -> None:
        self.project_name_input.setText(name)
        self.save_project_requested.emit(name)
        self._saved = True

    def _on_save_project(self) -> None:
        name = self.project_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, tr("qrexport.name_required_title"), tr("qrexport.name_required_msg"))
            return
        self._save_project(name)
        QMessageBox.information(self, tr("qrexport.project_saved_title"), tr("qrexport.project_saved_msg").format(name=name))

    def _on_done(self) -> None:
        
        if self._final_image is not None and not self._saved:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Question)
            box.setWindowTitle(tr("qrexport.unsaved_title"))
            box.setText(tr("qrexport.unsaved_msg"))
            save_button = box.addButton(tr("qrexport.unsaved_save"), QMessageBox.AcceptRole)
            discard_button = box.addButton(tr("qrexport.unsaved_discard"), QMessageBox.DestructiveRole)
            box.addButton(tr("qrexport.unsaved_cancel"), QMessageBox.RejectRole)
            box.setDefaultButton(save_button)
            box.exec()

            clicked = box.clickedButton()
            if clicked is save_button:
                name = self.project_name_input.text().strip() or self._default_project_name()
                self._save_project(name)
            elif clicked is not discard_button:
                return  # Cancelar: seguimos en la pantalla de exportar

        self.finished.emit()

    def retranslate(self) -> None:
        self.title_label.setText(tr("qrexport.title"))
        self.format_label.setText(tr("qrexport.format"))
        self.resolution_label.setText(tr("qrexport.resolution"))
        self.size_label.setText(tr("qrexport.size"))
        self.export_btn.setText(tr("qrexport.download"))
        self.print_btn.setText(tr("qrexport.print"))
        self.save_project_label.setText(tr("qrexport.save_project"))
        self.save_btn.setText(tr("qrexport.save_project_button"))
        self.back_btn.setText(tr("qrexport.back"))
        self.done_btn.setText(tr("qrexport.done"))
        self.custom_w.setPlaceholderText(tr("qrexport.width_placeholder"))
        self.custom_h.setPlaceholderText(tr("qrexport.height_placeholder"))
        self.preview.retranslate()
