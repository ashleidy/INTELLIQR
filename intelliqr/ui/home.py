from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Signal, Qt

from ui.i18n import tr
from ui import theme


class _ActionCard(QFrame):
    def __init__(self, icon: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(196)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setFixedSize(46, 46)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            f"font-size: 24px; background-color: {theme.PRIMARY_VERY_LIGHT};"
            f" border-radius: 14px;"
        )
        self.title_label = QLabel()
        self.title_label.setObjectName("H3")
        self.desc_label = QLabel()
        self.desc_label.setObjectName("Caption")
        self.desc_label.setWordWrap(True)

        self.button = QPushButton()
        self.button.setObjectName("PrimaryButton")

        layout.addWidget(icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.desc_label)
        layout.addStretch()
        layout.addWidget(self.button)

    def set_texts(self, title: str, desc: str, button_text: str) -> None:
        self.title_label.setText(title)
        self.desc_label.setText(desc)
        self.button.setText(button_text)


class HomeScreen(QWidget):
    create_qr_requested = Signal()
    create_barcode_requested = Signal()
    # open_qr_requested se eliminó: ya no hay lista de recientes desde la que emitirla.

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        self.header = QLabel()
        self.header.setObjectName("H1")
        self.free_badge = QLabel(tr("sidebar.free"))
        self.free_badge.setObjectName("BadgeSuccess")
        header_row.addWidget(self.header)
        header_row.addWidget(self.free_badge)
        header_row.addStretch()

        self.subtitle = QLabel()
        self.subtitle.setObjectName("Subtitle")
        layout.addLayout(header_row)
        layout.addWidget(self.subtitle)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        self.qr_card = _ActionCard("📱")
        self.qr_card.button.clicked.connect(self.create_qr_requested.emit)
        self.barcode_card = _ActionCard("🏷️")
        self.barcode_card.button.clicked.connect(self.create_barcode_requested.emit)
        cards_row.addWidget(self.qr_card)
        cards_row.addWidget(self.barcode_card)
        layout.addLayout(cards_row)
        layout.addStretch()

        self.retranslate()

    def retranslate(self) -> None:
        self.header.setText(tr("home.title"))
        self.subtitle.setText(tr("home.subtitle"))
        self.qr_card.set_texts(tr("home.qr_card.title"), tr("home.qr_card.desc"), tr("home.qr_card.button"))
        self.barcode_card.set_texts(tr("home.barcode_card.title"), tr("home.barcode_card.desc"), tr("home.barcode_card.button"))
        self.free_badge.setText(tr("sidebar.free"))
