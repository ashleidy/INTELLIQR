"""
Pantalla de impresión (sección 45 del spec): imprimir un código QR o de
barras guardado (o una imagen cargada), eligiendo impresora predeterminada,
tamaño de papel, orientación, márgenes, tamaño y cantidad de copias, con
vista previa antes de imprimir.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QSpinBox, QDoubleSpinBox, QRadioButton, QButtonGroup, QFileDialog,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QImage
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PIL import Image

from core.print_engine.print_layout import compute_layout, PrintLayoutOptions
from core.qr_engine.generator import QRGenerator, QRDesignOptions
from core.qr_engine.designer import FrameOptions, apply_frame
from core.barcode_engine.generator import BarcodeGenerator
from database.repositories.qr_repository import QRRepository
from database.repositories.barcode_repository import BarcodeRepository
from ui.qr.qr_preview import QRPreviewWidget, pil_to_qimage
from ui.i18n import tr

MM_PER_INCH = 25.4


class PrintScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._qr_repo = QRRepository()
        self._barcode_repo = BarcodeRepository()
        self._generator = QRGenerator()
        self._barcode_generator = BarcodeGenerator()
        self._current_image: Image.Image | None = None
        self._loaded_file_image: Image.Image | None = None

        root = QHBoxLayout(self)
        left = QVBoxLayout()

        self.title_label = QLabel()
        self.title_label.setObjectName("H1")
        left.addWidget(self.title_label)
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("Subtitle")
        left.addWidget(self.subtitle_label)

        # ---- Qué imprimir ----
        self.what_label = self._section_label("")
        left.addWidget(self.what_label)
        source_row = QHBoxLayout()
        self.source_group = QButtonGroup(self)
        self.radio_qr = QRadioButton()
        self.radio_barcode = QRadioButton()
        self.radio_file = QRadioButton()
        self.radio_qr.setChecked(True)
        for i, rb in enumerate([self.radio_qr, self.radio_barcode, self.radio_file]):
            self.source_group.addButton(rb, i)
            source_row.addWidget(rb)
        self.source_group.buttonClicked.connect(self._on_source_changed)
        left.addLayout(source_row)

        self.item_combo = QComboBox()
        self.item_combo.currentIndexChanged.connect(self._on_item_selected)
        left.addWidget(self.item_combo)

        self.load_file_btn = QPushButton()
        self.load_file_btn.setObjectName("SecondaryButton")
        self.load_file_btn.clicked.connect(self._on_load_file)
        self.load_file_btn.hide()
        left.addWidget(self.load_file_btn)

        # ---- Papel ----
        self.paper_label = self._section_label("")
        left.addWidget(self.paper_label)
        paper_row = QHBoxLayout()
        self.size_label = QLabel()
        paper_row.addWidget(self.size_label)
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4", "Carta", "Personalizado"])
        self.page_size_combo.currentTextChanged.connect(self._on_changed)
        paper_row.addWidget(self.page_size_combo)
        self.orientation_label = QLabel()
        paper_row.addWidget(self.orientation_label)
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["vertical", "horizontal"])
        self.orientation_combo.currentTextChanged.connect(self._on_changed)
        paper_row.addWidget(self.orientation_combo)
        left.addLayout(paper_row)

        margin_row = QHBoxLayout()
        self.margin_label = QLabel()
        margin_row.addWidget(self.margin_label)
        self.margin_spin = QDoubleSpinBox()
        self.margin_spin.setRange(0, 50)
        self.margin_spin.setValue(10)
        self.margin_spin.valueChanged.connect(self._on_changed)
        margin_row.addWidget(self.margin_spin)
        left.addLayout(margin_row)

        # ---- Tamaño y cantidad ----
        self.size_qty_label = self._section_label("")
        left.addWidget(self.size_qty_label)
        size_row = QHBoxLayout()
        self.item_size_label = QLabel()
        size_row.addWidget(self.item_size_label)
        self.item_size_spin = QDoubleSpinBox()
        self.item_size_spin.setRange(10, 200)
        self.item_size_spin.setValue(50)
        self.item_size_spin.valueChanged.connect(self._on_changed)
        size_row.addWidget(self.item_size_spin)
        left.addLayout(size_row)

        copies_row = QHBoxLayout()
        self.copies_label = QLabel()
        copies_row.addWidget(self.copies_label)
        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 500)
        self.copies_spin.setValue(1)
        self.copies_spin.valueChanged.connect(self._on_changed)
        copies_row.addWidget(self.copies_spin)
        left.addLayout(copies_row)

        self.layout_info_label = QLabel("")
        self.layout_info_label.setObjectName("Caption")
        self.layout_info_label.setWordWrap(True)
        left.addWidget(self.layout_info_label)

        # ---- Acciones ----
        actions_row = QHBoxLayout()
        self.preview_btn = QPushButton()
        self.preview_btn.setObjectName("SecondaryButton")
        self.preview_btn.clicked.connect(self._on_preview)
        self.print_btn = QPushButton()
        self.print_btn.setObjectName("PrimaryButton")
        self.print_btn.clicked.connect(self._on_print)
        actions_row.addWidget(self.preview_btn)
        actions_row.addWidget(self.print_btn)
        left.addLayout(actions_row)
        left.addStretch()

        right = QVBoxLayout()
        self.preview = QRPreviewWidget()
        right.addWidget(self.preview)
        right.addStretch()

        root.addLayout(left, 3)
        root.addLayout(right, 2)

        self.retranslate()

    def retranslate(self) -> None:
        self.title_label.setText(tr("print.title"))
        self.subtitle_label.setText(tr("print.subtitle"))
        self.what_label.setText(tr("print.what"))
        self.radio_qr.setText(tr("print.source_qr"))
        self.radio_barcode.setText(tr("print.source_barcode"))
        self.radio_file.setText(tr("print.source_file"))
        self.load_file_btn.setText(tr("print.choose_file"))
        self.paper_label.setText(tr("print.paper"))
        self.size_label.setText(tr("print.size"))
        self.orientation_label.setText(tr("print.orientation"))
        self.margin_label.setText(tr("print.margin"))
        self.size_qty_label.setText(tr("print.size_and_quantity"))
        self.item_size_label.setText(tr("print.item_size"))
        self.copies_label.setText(tr("print.copies"))
        self.preview_btn.setText(tr("print.preview"))
        self.print_btn.setText(tr("print.print_button"))
        self.preview.title_label.setText(tr("print.preview_page_title"))
        if self._current_image is None:
            self.preview.show_placeholder(tr("print.preview_placeholder"))


    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("H3")
        return label

    def refresh(self) -> None:
        """Vuelve a cargar la lista de QR/códigos de barras guardados. Se llama al navegar a esta pantalla."""
        self._on_source_changed()

    # ---------- Selección de origen ----------
    def _on_source_changed(self, *args) -> None:
        self.item_combo.clear()
        is_file = self.radio_file.isChecked()
        self.item_combo.setVisible(not is_file)
        self.load_file_btn.setVisible(is_file)
        self._current_image = None

        if self.radio_qr.isChecked():
            for qr in self._qr_repo.list_all():
                self.item_combo.addItem(f"{qr.name} ({qr.type_id.upper()})", ("qr", qr.id))
        elif self.radio_barcode.isChecked():
            for bc in self._barcode_repo.list_all():
                self.item_combo.addItem(f"{bc.name} ({bc.barcode_type.upper()})", ("barcode", bc.id))

        self._on_item_selected()

    def _on_item_selected(self, *args) -> None:
        data = self.item_combo.currentData()
        if not data:
            self._current_image = None
            self._update_preview()
            return
        kind, item_id = data
        try:
            if kind == "qr":
                record = self._qr_repo.get(item_id)
                if record is None:
                    return
                design = record.design
                design_options = QRDesignOptions(
                    pattern=design.pattern, corner_style=design.corner_style,
                    fg_color=design.fg_color, bg_color=design.bg_color,
                    gradient_enabled=design.gradient_enabled, gradient_start=design.gradient_start,
                    gradient_end=design.gradient_end, logo_path=design.logo_path,
                    logo_size_ratio=design.logo_size_ratio,
                    transparent_background=design.transparent_background,
                ) if design else QRDesignOptions()
                result = self._generator.generate(record.payload, design_options)
                frame_options = FrameOptions(
                    style=design.frame_style if design else "ninguno",
                    text=design.frame_text if design else "ESCANÉAME",
                    frame_color=design.frame_color if design else "#2563EB",
                    text_color=design.frame_text_color if design else "#FFFFFF",
                )
                self._current_image = apply_frame(result.image, frame_options)
            elif kind == "barcode":
                record = self._barcode_repo.get(item_id)
                if record is None:
                    return
                result = self._barcode_generator.generate(record.barcode_type, record.value)
                self._current_image = result.image
        except Exception:
            self._current_image = None
            QMessageBox.warning(self, "No pudimos preparar el código", "Ocurrió un problema al regenerar este código para imprimir.")
        self._update_preview()

    def _on_load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Elegir imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if not path:
            return
        try:
            self._current_image = Image.open(path).convert("RGB")
        except Exception:
            QMessageBox.warning(self, "No pudimos abrir la imagen", "Revisa que el archivo sea una imagen válida.")
            return
        self._update_preview()

    # ---------- Layout / vista previa ----------
    def _build_layout_options(self) -> PrintLayoutOptions:
        return PrintLayoutOptions(
            page_size=self.page_size_combo.currentText(),
            orientation=self.orientation_combo.currentText(),
            margin_mm=self.margin_spin.value(),
            item_size_mm=self.item_size_spin.value(),
            copies=self.copies_spin.value(),
        )

    def _on_changed(self, *args) -> None:
        self._update_preview()

    def _update_preview(self) -> None:
        if self._current_image is None:
            self.preview.show_placeholder(tr("print.preview_placeholder"))
            self.layout_info_label.setText("")
            return

        layout = compute_layout(self._build_layout_options())
        self.layout_info_label.setText(
            f"{layout.columns} × {layout.rows} = {layout.per_page} copias por página "
            f"→ {layout.pages_needed} página(s) para {self.copies_spin.value()} copia(s)."
        )

        # Vista previa simplificada: solo el código individual (la cuadrícula
        # completa se ve en 'Vista previa' con QPrintPreviewDialog).
        self.preview.show_image(self._current_image)

    # ---------- Impresión real ----------
    def _paint_page(self, printer: QPrinter) -> None:
        if self._current_image is None:
            return
        layout = compute_layout(self._build_layout_options())
        dpi = printer.resolution()
        mm_to_px = dpi / MM_PER_INCH

        qimage = pil_to_qimage(self._current_image)
        item_size_px = int(layout.item_size_mm * mm_to_px) if hasattr(layout, "item_size_mm") else int(self.item_size_spin.value() * mm_to_px)
        scaled = qimage.scaled(item_size_px, item_size_px, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        painter = QPainter(printer)
        remaining = self.copies_spin.value()
        first_page = True
        while remaining > 0:
            if not first_page:
                printer.newPage()
            first_page = False
            for x_mm, y_mm in layout.positions_per_page:
                if remaining <= 0:
                    break
                x_px, y_px = x_mm * mm_to_px, y_mm * mm_to_px
                painter.drawImage(int(x_px), int(y_px), scaled)
                remaining -= 1
        painter.end()

    def _configure_printer(self, printer: QPrinter) -> None:
        from PySide6.QtGui import QPageLayout, QPageSize
        orientation = QPageLayout.Landscape if self.orientation_combo.currentText() == "horizontal" else QPageLayout.Portrait
        page_size = QPageSize.Letter if self.page_size_combo.currentText() == "Carta" else QPageSize.A4
        printer.setPageSize(QPageSize(page_size))
        printer.setPageOrientation(orientation)

    def _on_preview(self) -> None:
        if self._current_image is None:
            QMessageBox.warning(self, "Nada que imprimir", "Selecciona primero un código o carga una imagen.")
            return
        printer = QPrinter(QPrinter.HighResolution)
        self._configure_printer(printer)
        dialog = QPrintPreviewDialog(printer, self)
        dialog.paintRequested.connect(self._paint_page)
        dialog.exec()

    def _on_print(self) -> None:
        if self._current_image is None:
            QMessageBox.warning(self, "Nada que imprimir", "Selecciona primero un código o carga una imagen.")
            return
        printer = QPrinter(QPrinter.HighResolution)
        self._configure_printer(printer)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.Accepted:
            return
        self._paint_page(printer)
