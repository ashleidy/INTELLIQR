"""Pantalla 'Mis códigos de barra' (análoga a Mis QR, sección 20 ampliada)."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Signal, Qt

from database.repositories.barcode_repository import BarcodeRepository
from core.barcode_engine.generator import BarcodeGenerator, TYPES
from ui.qr.qr_preview import pil_to_qpixmap
from ui.i18n import tr
from ui import theme


def _build_thumbnail(barcode, size: int = 56) -> object:
    """Genera una miniatura real del código de barras guardado, con su
    propio tipo y escala — igual que 'Mis QR' hace con sus diseños."""
    try:
        generator = BarcodeGenerator()
        result = generator.generate(
            barcode.barcode_type, barcode.value, show_text=False,
            scale=min(barcode.image_scale or 2, 3),
        )
        pixmap = pil_to_qpixmap(result.image)
        return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    except Exception:
        return None


class _BarcodeRow(QFrame):
    open_requested = Signal(int)
    duplicate_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, barcode, parent=None):
        super().__init__(parent)
        self.barcode_id = barcode.id
        self.setObjectName("Card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        thumb_label = QLabel()
        thumb_label.setFixedSize(56, 56)
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setStyleSheet(
            f"background-color: white; border: 1px solid {theme.BORDER}; border-radius: 8px;"
        )
        pixmap = _build_thumbnail(barcode)
        if pixmap is not None:
            thumb_label.setPixmap(pixmap)
        else:
            thumb_label.setText("▥")
            thumb_label.setStyleSheet(thumb_label.styleSheet() + "font-size: 22px;")
        layout.addWidget(thumb_label)

        info = QVBoxLayout()
        info.setSpacing(2)
        name_label = QLabel(barcode.name)
        name_label.setObjectName("H3")
        info.addWidget(name_label)

        # Contenido codificado (si tiene alguno) — antes esta fila solo
        # mostraba nombre, tipo y fecha, sin ningún indicio de qué había
        # dentro del código.
        if barcode.value:
            content_label = QLabel(barcode.value)
            content_label.setObjectName("Caption")
            content_label.setWordWrap(True)
            info.addWidget(content_label)

        type_display = TYPES[barcode.barcode_type].display_name if barcode.barcode_type in TYPES else barcode.barcode_type.upper()
        meta_label = QLabel(f"{tr('barcodelist.type_prefix')}: {type_display}   ·   "
                             f"{tr('barcodelist.created_prefix')}: {barcode.created_at.strftime('%d/%m/%Y')}")
        meta_label.setObjectName("Caption")
        info.addWidget(meta_label)
        layout.addLayout(info, 1)

        open_btn = QPushButton(tr("barcodelist.open"))
        open_btn.setObjectName("PrimaryButton")
        open_btn.clicked.connect(lambda: self.open_requested.emit(self.barcode_id))
        dup_btn = QPushButton(tr("barcodelist.duplicate"))
        dup_btn.setObjectName("SecondaryButton")
        dup_btn.clicked.connect(lambda: self.duplicate_requested.emit(self.barcode_id))
        del_btn = QPushButton(tr("barcodelist.delete"))
        del_btn.setObjectName("SecondaryButton")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.barcode_id))

        layout.addWidget(open_btn)
        layout.addWidget(dup_btn)
        layout.addWidget(del_btn)


class BarcodeListScreen(QWidget):
    open_barcode_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._repo = BarcodeRepository()

        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.header.setObjectName("H1")
        layout.addWidget(self.header)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self._filter)
        search_row.addWidget(self.search_input)
        layout.addLayout(search_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(10)
        self.list_layout.addStretch()
        scroll.setWidget(self.list_container)
        layout.addWidget(scroll)

        self.retranslate()

    def retranslate(self) -> None:
        self.header.setText(tr("barcodelist.title"))
        self.search_input.setPlaceholderText(tr("barcodelist.search"))
        self.refresh()

    def refresh(self) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._all_barcodes = self._repo.list_all()
        if not self._all_barcodes:
            empty = QLabel(tr("barcodelist.empty"))
            empty.setObjectName("Caption")
            self.list_layout.insertWidget(0, empty)
            return

        for barcode in self._all_barcodes:
            row = _BarcodeRow(barcode)
            row.open_requested.connect(self.open_barcode_requested.emit)
            row.duplicate_requested.connect(self._on_duplicate)
            row.delete_requested.connect(self._on_delete)
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)

    def _filter(self, text: str) -> None:
        text = text.lower().strip()
        for i in range(self.list_layout.count() - 1):
            widget = self.list_layout.itemAt(i).widget()
            if isinstance(widget, _BarcodeRow):
                bc = next((b for b in self._all_barcodes if b.id == widget.barcode_id), None)
                matches = bc is not None and (
                    text in bc.name.lower() or text in (bc.value or "").lower()
                )
                widget.setVisible(matches)

    def _on_duplicate(self, barcode_id: int) -> None:
        bc = self._repo.get(barcode_id)
        if bc:
            self._repo.duplicate(barcode_id, f"{bc.name} {tr('barcodelist.copy_suffix')}")
            self.refresh()

    def _on_delete(self, barcode_id: int) -> None:
        confirm = QMessageBox.question(self, tr("barcodelist.delete_confirm_title"), tr("barcodelist.delete_confirm_msg"))
        if confirm == QMessageBox.Yes:
            self._repo.delete(barcode_id)
            self.refresh()
