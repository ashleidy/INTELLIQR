"""Pantalla 'Mis códigos QR' (sección 20 del spec), con miniatura real."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QPixmap, QImage
from ui.qr.qr_preview import pil_to_qpixmap

from database.repositories.qr_repository import QRRepository
from core.qr_engine.generator import QRGenerator, QRDesignOptions
from core.qr_engine.designer import FrameOptions, apply_frame
from ui.i18n import tr
from ui import theme

_TYPE_ICONS = {
    "url": "🔗", "google_maps": "📍", "whatsapp": "💬", "phone": "📞", "sms": "✉️",
    "email": "📧", "vcard": "👤", "text": "📝", "wifi": "📶",
    "event": "📅", "location": "🧭", "sepa": "🏦",
}


def _build_thumbnail(qr, size: int = 56) -> QPixmap | None:
    """Genera una miniatura real del QR guardado (con su propio diseño),
    en vez de solo mostrar texto — así se reconoce de un vistazo."""
    try:
        generator = QRGenerator()
        design = qr.design
        # Ojo: aquí faltaban logo y fondo transparente. El diseño guardado
        # debe verse "tal cual" en la miniatura, no una versión simplificada.
        design_options = QRDesignOptions(
            pattern=design.pattern, corner_style=design.corner_style,
            fg_color=design.fg_color, bg_color=design.bg_color,
            gradient_enabled=design.gradient_enabled, gradient_start=design.gradient_start,
            gradient_end=design.gradient_end,
            logo_path=design.logo_path, logo_size_ratio=design.logo_size_ratio,
            transparent_background=design.transparent_background,
            box_size=4, border=1,
        ) if design else QRDesignOptions(box_size=4, border=1)
        result = generator.generate(qr.payload, design_options)
        image = result.image
        if design and design.frame_style and design.frame_style != "ninguno":
            frame_options = FrameOptions(style=design.frame_style, text=design.frame_text,
                                          frame_color=design.frame_color, text_color=design.frame_text_color)
            image = apply_frame(image, frame_options)
        pixmap = pil_to_qpixmap(image)
        return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    except Exception:
        return None


class _QRRow(QFrame):
    open_requested = Signal(int)
    duplicate_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, qr, parent=None):
        super().__init__(parent)
        self.qr_id = qr.id
        self.setObjectName("Card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        thumb_label = QLabel()
        thumb_label.setFixedSize(56, 56)
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setStyleSheet(f"background-color: white; border: 1px solid {theme.BORDER}; border-radius: 8px;")
        pixmap = _build_thumbnail(qr)
        if pixmap is not None:
            thumb_label.setPixmap(pixmap)
        else:
            thumb_label.setText(_TYPE_ICONS.get(qr.type_id, "▦"))
            thumb_label.setStyleSheet(thumb_label.styleSheet() + "font-size: 22px;")
        layout.addWidget(thumb_label)

        info = QVBoxLayout()
        info.setSpacing(2)
        name_row = QHBoxLayout()
        name_row.setSpacing(6)
        type_badge = QLabel(_TYPE_ICONS.get(qr.type_id, "▦"))
        type_badge.setStyleSheet("font-size: 14px;")
        name_label = QLabel(qr.name)
        name_label.setObjectName("H3")
        name_row.addWidget(type_badge)
        name_row.addWidget(name_label, 1)
        info.addLayout(name_row)
        meta_label = QLabel(
            f"{tr('qrlist.type_prefix')}: {qr.type_id.upper()}   ·   "
            f"{tr('qrlist.created_prefix')}: {qr.created_at.strftime('%d/%m/%Y')}"
        )
        meta_label.setObjectName("Caption")
        info.addWidget(meta_label)
        layout.addLayout(info, 1)

        open_btn = QPushButton(tr("qrlist.open"))
        open_btn.setObjectName("PrimaryButton")
        open_btn.clicked.connect(lambda: self.open_requested.emit(self.qr_id))
        dup_btn = QPushButton(tr("qrlist.duplicate"))
        dup_btn.setObjectName("SecondaryButton")
        dup_btn.clicked.connect(lambda: self.duplicate_requested.emit(self.qr_id))
        del_btn = QPushButton(tr("qrlist.delete"))
        del_btn.setObjectName("SecondaryButton")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.qr_id))

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        buttons_row.addWidget(open_btn)
        buttons_row.addWidget(dup_btn)
        buttons_row.addWidget(del_btn)
        layout.addLayout(buttons_row)


class QRListScreen(QWidget):
    open_qr_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._repo = QRRepository()

        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.header.setObjectName("H1")
        layout.addWidget(self.header)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("qrlist.search"))
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
        self.refresh()

    def retranslate(self) -> None:
        self.header.setText(tr("qrlist.title"))
        self.search_input.setPlaceholderText(tr("qrlist.search"))
        self.refresh()

    def refresh(self) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._all_qrs = self._repo.list_all()
        if not self._all_qrs:
            empty = QLabel(tr("qrlist.empty"))
            empty.setObjectName("Caption")
            self.list_layout.insertWidget(0, empty)
            return

        for qr in self._all_qrs:
            row = _QRRow(qr)
            row.open_requested.connect(self.open_qr_requested.emit)
            row.duplicate_requested.connect(self._on_duplicate)
            row.delete_requested.connect(self._on_delete)
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)

    def _filter(self, text: str) -> None:
        text = text.lower().strip()
        for i in range(self.list_layout.count() - 1):
            widget = self.list_layout.itemAt(i).widget()
            if isinstance(widget, _QRRow):
                qr = next((q for q in self._all_qrs if q.id == widget.qr_id), None)
                widget.setVisible(qr is not None and text in qr.name.lower())

    def _on_duplicate(self, qr_id: int) -> None:
        qr = self._repo.get(qr_id)
        if qr:
            self._repo.duplicate(qr_id, f"{qr.name} {tr('qrlist.copy_suffix')}")
            self.refresh()

    def _on_delete(self, qr_id: int) -> None:
        confirm = QMessageBox.question(self, tr("qrlist.delete_confirm_title"), tr("qrlist.delete_confirm_msg"))
        if confirm == QMessageBox.Yes:
            self._repo.delete(qr_id)
            self.refresh()
