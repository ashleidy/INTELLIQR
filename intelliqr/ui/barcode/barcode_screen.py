
from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QCheckBox, QFileDialog, QMessageBox, QFrame, QScrollArea, QSlider
)
from PySide6.QtCore import QTimer, Qt

from core.barcode_engine.generator import BarcodeGenerator, TYPES, CATEGORIES, TWO_D_TYPES
from core.barcode_engine.validator import validate_barcode
from ui.qr.qr_preview import QRPreviewWidget
from database.repositories.barcode_repository import BarcodeRepository
from app.config import EXPORTS_DIR
from ui import theme
from ui.i18n import tr


_CATEGORY_KEYS = {
    "Códigos lineales": "barcode.category.codigos_lineales",
    "EAN / UPC": "barcode.category.ean_upc",
    "GS1 DataBar": "barcode.category.gs1_databar",
    "Códigos ISBN": "barcode.category.codigos_isbn",
    "Códigos de sanidad": "barcode.category.codigos_sanidad",
    "Códigos 2D": "barcode.category.codigos_2d",
    "Códigos GS1 2D": "barcode.category.codigos_gs1_2d",
    "Códigos postales": "barcode.category.codigos_postales",
}


class BarcodeScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._generator = BarcodeGenerator()
        self._repo = BarcodeRepository()
        self._current_image = None
        self._current_value = ""
        self._editing_barcode_id: int | None = None

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(self._update_preview)

        root = QHBoxLayout(self)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left = QWidget()
        left_layout = QVBoxLayout(left)

        self.title_label = QLabel()
        self.title_label.setObjectName("H1")
        left_layout.addWidget(self.title_label)
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("Subtitle")
        left_layout.addWidget(self.subtitle_label)

        self.type_section_label = self._section_label("")
        left_layout.addWidget(self.type_section_label)
        self.type_combo = QComboBox()
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        left_layout.addWidget(self.type_combo)

        self.help_card = QFrame()
        self.help_card.setObjectName("Card")
        help_layout = QVBoxLayout(self.help_card)
        self.help_text_label = QLabel("")
        self.help_text_label.setWordWrap(True)
        self.help_text_label.setObjectName("Caption")
        self.example_label = QLabel("")
        self.example_label.setWordWrap(True)
        self.example_label.setStyleSheet(f"color: {theme.PRIMARY}; font-weight: 600; font-family: monospace;")
        self.use_example_btn = QPushButton()
        self.use_example_btn.setObjectName("SecondaryButton")
        self.use_example_btn.clicked.connect(self._use_example)
        help_layout.addWidget(self.help_text_label)
        help_layout.addWidget(self.example_label)
        help_layout.addWidget(self.use_example_btn)
        left_layout.addWidget(self.help_card)

        self.content_section_label = self._section_label("")
        left_layout.addWidget(self.content_section_label)
        self.value_input = QLineEdit()
        self.value_input.textChanged.connect(self._on_changed)
        left_layout.addWidget(self.value_input)

        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        left_layout.addWidget(self.error_label)

        self.info_label = QLabel("")
        self.info_label.setObjectName("Caption")
        self.info_label.hide()
        left_layout.addWidget(self.info_label)

        self.show_text_check = QCheckBox()
        self.show_text_check.setChecked(True)
        self.show_text_check.stateChanged.connect(self._on_changed)
        left_layout.addWidget(self.show_text_check)

        self.image_size_label = self._section_label("")
        left_layout.addWidget(self.image_size_label)
        self.image_size_slider = QSlider(Qt.Horizontal)
        self.image_size_slider.setRange(1, 8)
        self.image_size_slider.setValue(2)
        self.image_size_slider.valueChanged.connect(self._on_changed)
        left_layout.addWidget(self.image_size_slider)

        self.name_section_label = self._section_label("")
        left_layout.addWidget(self.name_section_label)
        self.name_input = QLineEdit()
        left_layout.addWidget(self.name_input)

        buttons_row = QHBoxLayout()
        self.save_btn = QPushButton()
        self.save_btn.setObjectName("SecondaryButton")
        self.save_btn.clicked.connect(self._on_save)
        self.export_png_btn = QPushButton()
        self.export_png_btn.setObjectName("SecondaryButton")
        self.export_png_btn.clicked.connect(lambda: self._on_export("PNG"))
        self.export_pdf_btn = QPushButton()
        self.export_pdf_btn.setObjectName("PrimaryButton")
        self.export_pdf_btn.clicked.connect(lambda: self._on_export("PDF"))
        buttons_row.addWidget(self.save_btn)
        buttons_row.addWidget(self.export_png_btn)
        buttons_row.addWidget(self.export_pdf_btn)
        left_layout.addLayout(buttons_row)
        left_layout.addStretch()

        left_scroll.setWidget(left)
        root.addWidget(left_scroll, 3)

        right = QVBoxLayout()
        self.preview = QRPreviewWidget()
        right.addWidget(self.preview)
        right.addStretch()
        root.addLayout(right, 2)

        self.retranslate()

    def _default_name(self) -> str:
        """Nombre con el que se guardará/exportará el barcode:
        1) lo que el usuario escribió en 'Name (to save)',
        2) si está vacío, el mismo patrón que usa _on_save: '<Tipo> <valor>'."""
        name = self.name_input.text().strip()
        if name:
            return name
        return f"{TYPES[self._current_type()].display_name} {self._current_value}".strip()

    def retranslate(self) -> None:
        self.title_label.setText(tr("barcode.title"))
        self.subtitle_label.setText(tr("barcode.subtitle"))
        self.type_section_label.setText(tr("barcode.type_label"))
        self.content_section_label.setText(tr("barcode.content_label"))
        self.name_section_label.setText(tr("barcode.name_label"))
        self.name_input.setPlaceholderText(tr("barcode.name_placeholder"))
        self.show_text_check.setText(tr("barcode.show_text"))
        self.image_size_label.setText(tr("barcode.image_size"))
        self.use_example_btn.setText(tr("barcode.use_example"))
        self.save_btn.setText(tr("barcode.save"))
        self.export_png_btn.setText(tr("barcode.export_png"))
        self.export_pdf_btn.setText(tr("barcode.export_pdf"))
        self.preview.title_label.setText(tr("barcode.preview_title"))
        self._rebuild_type_combo()

    def _rebuild_type_combo(self) -> None:
        current_type = self.type_combo.currentData()
        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        for category, type_ids in CATEGORIES.items():
            category_label = tr(_CATEGORY_KEYS.get(category, category))
            self.type_combo.addItem(f"── {category_label} ──")
            idx = self.type_combo.count() - 1
            self.type_combo.model().item(idx).setEnabled(False)
            for type_id in type_ids:
                self.type_combo.addItem(f"  {TYPES[type_id].display_name}", type_id)
        if current_type:
            self.type_combo.setCurrentIndex(self.type_combo.findData(current_type))
        else:
            self.type_combo.setCurrentIndex(1)
        self.type_combo.blockSignals(False)
        self._on_type_changed()

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("H3")
        return label

    def _current_type(self) -> str:
        return self.type_combo.currentData()

    def _on_type_changed(self, *args) -> None:
        info = TYPES[self._current_type()]
        is_2d = self._current_type() in TWO_D_TYPES

        self.help_text_label.setText(info.help_text)
        self.example_label.setText(f"{tr('barcode.example_prefix')}: {info.example}")
        self.value_input.setPlaceholderText(info.placeholder)
        self.show_text_check.setEnabled(not is_2d)
        self.show_text_check.setVisible(not is_2d)

        self.error_label.hide()
        self.info_label.hide()
        self._on_changed()

    def _use_example(self) -> None:
        info = TYPES[self._current_type()]
        self.value_input.setText(info.placeholder)

    def _on_changed(self, *args) -> None:
        self.error_label.hide()
        self._debounce.start()

    def _update_preview(self) -> None:
        barcode_type = self._current_type()
        value = self.value_input.text().strip()
        if not value:
            self.preview.show_placeholder(tr("qrcontent.preview_placeholder"))
            self._current_image = None
            return

        result = validate_barcode(barcode_type, value)
        if not result.is_valid:
            self.error_label.setText(result.message)
            self.error_label.show()
            self.preview.show_placeholder(tr("qrcontent.error_generic"))
            self._current_image = None
            return

        try:
            gen_result = self._generator.generate(barcode_type, value, self.show_text_check.isChecked(),
                                                    scale=self.image_size_slider.value())
            self._current_image = gen_result.image
            self._current_value = value
            self.preview.show_image(gen_result.image)
        except ValueError as exc:
            self.error_label.setText(str(exc))
            self.error_label.show()
            self.preview.show_placeholder(tr("qrcontent.error_generic"))
            self._current_image = None

    def _on_save(self) -> None:
        if self._current_image is None:
            QMessageBox.warning(self, tr("barcode.nothing_to_save_title"),
                                tr("barcode.nothing_to_save_msg"))
            return
        name = self._default_name()
        self._editing_barcode_id = self._repo.save(
            name=name, barcode_type=self._current_type(), value=self._current_value,
            barcode_id=self._editing_barcode_id, image_scale=self.image_size_slider.value(),
        )
        QMessageBox.information(self, tr("barcode.save_success_title"),
                                tr("barcode.save_success_msg"))

    def reset(self) -> None:
        """Limpia el formulario para crear un código nuevo (no editar uno existente)."""
        self._editing_barcode_id = None
        self.name_input.clear()
        self.value_input.clear()

    def open_existing(self, barcode_id: int) -> None:
        """Carga un código de barras guardado (desde 'Mis códigos de barra') para verlo o editarlo."""
        record = self._repo.get(barcode_id)
        if record is None:
            return
        self._editing_barcode_id = record.id
        self.name_input.setText(record.name)
        idx = self.type_combo.findData(record.barcode_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.image_size_slider.setValue(record.image_scale or 2)
        self.value_input.setText(record.value)

    def _on_export(self, fmt: str) -> None:
        if self._current_image is None:
            QMessageBox.warning(self, tr("barcode.nothing_to_export_title"),
                                tr("barcode.nothing_to_export_msg"))
            return

        ext = {"PNG": "png", "PDF": "pdf"}[fmt]

        # NUEVO: usar el nombre asignado (o su fallback) en vez de "barcode".
        from re import sub as _re_sub  # evita añadir import al módulo si no lo tienes
        safe = _re_sub(r'[<>:"/\\|?*\x00-\x1f]', "_", self._default_name()).strip().strip(".") or "barcode"

        default_path = str(EXPORTS_DIR / f"{safe}.{ext}")

        title = tr("barcode.export_png") if fmt == "PNG" else tr("barcode.export_pdf")
        path, _ = QFileDialog.getSaveFileName(self, title, default_path, f"Archivos {fmt} (*.{ext})")
        if not path:
            return

        try:
            if fmt == "PNG":
                self._current_image.save(path, format="PNG", dpi=(300, 300))
            elif fmt == "PDF":
                self._export_pdf(path)
            QMessageBox.information(self, tr("barcode.export_done_title"),
                                    tr("barcode.export_done_msg"))
        except Exception:
            QMessageBox.warning(self, tr("barcode.export_fail_title"),
                                tr("barcode.export_fail_msg"))

    def _export_pdf(self, path: str) -> None:
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        c = pdf_canvas.Canvas(path, pagesize=A4)
        page_w, page_h = A4
        tmp_png = Path(path).with_suffix(".tmp.png")
        self._current_image.save(tmp_png, format="PNG", dpi=(300, 300))
        img_w = 8 * cm
        img_h = img_w * (self._current_image.height / self._current_image.width)
        c.drawImage(str(tmp_png), (page_w - img_w) / 2, (page_h - img_h) / 2, width=img_w, height=img_h)
        c.showPage()
        c.save()
        tmp_png.unlink(missing_ok=True)
