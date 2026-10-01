"""Pantalla de selección de tipo de QR, agrupada por categorías (secciones 8-9)."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from qr_types.registry import get_categories
from ui.i18n import tr

_ICONS = {
    "link": "🔗", "map": "📍", "whatsapp": "💬", "phone": "📞", "sms": "✉️",
    "mail": "📧", "contact": "👤", "text": "📝", "wifi": "📶",
    "calendar": "📅", "location": "🧭", "bank": "🏦",
}

# Las categorías/nombres viven en español dentro de qr_types (son objetos de
# dominio puro, sin dependencia de Qt/i18n). Este mapa traduce esas cadenas
# fijas a claves de traducción para mostrarlas en el idioma elegido.
_CATEGORY_KEYS = {
    "Internet": "category.internet",
    "Comunicación": "category.comunicacion",
    "Contacto": "category.contacto",
    "Conectividad": "category.conectividad",
    "Eventos": "category.eventos",
    "Banca": "category.banca",
}


class QRTypeCard(QFrame):
    selected = Signal(str)

    def __init__(self, type_id: str, icon_key: str, parent=None):
        super().__init__(parent)
        self.type_id = type_id
        self.setObjectName("Card")
        # Antes: setFixedSize(220, 160). Con una altura fija, una descripción
        # más larga (o el texto en inglés, o un tamaño de letra más grande
        # desde Configuración) se recortaba y llegaba a superponerse con el
        # botón "Seleccionar". Ahora solo fijamos el ancho (para que la
        # cuadrícula quede alineada) y dejamos que la altura crezca según
        # el contenido, con un mínimo razonable para que no se vean tarjetas
        # demasiado chicas cuando el texto es corto.
        self.setFixedWidth(230)
        self.setMinimumHeight(180)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        icon_label = QLabel(_ICONS.get(icon_key, "▦"))
        icon_label.setStyleSheet("font-size: 26px;")

        self.title_label = QLabel()
        self.title_label.setObjectName("H3")
        self.title_label.setWordWrap(True)

        self.desc_label = QLabel()
        self.desc_label.setObjectName("Caption")
        self.desc_label.setWordWrap(True)

        self.button = QPushButton()
        self.button.setObjectName("SecondaryButton")
        self.button.clicked.connect(lambda: self.selected.emit(self.type_id))

        layout.addWidget(icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.desc_label)
        layout.addStretch()
        layout.addWidget(self.button)

        self.retranslate()

    def retranslate(self) -> None:
        self.title_label.setText(tr(f"qrtype.{self.type_id}.name"))
        self.desc_label.setText(tr(f"qrtype.{self.type_id}.desc"))
        self.button.setText(tr("qrselector.select_button"))

    def mousePressEvent(self, event):
        self.selected.emit(self.type_id)
        super().mousePressEvent(event)


class QRTypeSelector(QWidget):
    """Emite `type_chosen(type_id)` cuando el usuario elige un tipo."""
    type_chosen = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)

        self.header = QLabel()
        self.header.setObjectName("H2")
        outer.addWidget(self.header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        container_layout = QVBoxLayout(container)

        self._category_labels: list[tuple[QLabel, str]] = []
        self._cards: list[QRTypeCard] = []

        for category, types in get_categories().items():
            cat_label = QLabel()
            cat_label.setObjectName("Caption")
            self._category_labels.append((cat_label, category))
            container_layout.addWidget(cat_label)

            grid = QGridLayout()
            grid.setSpacing(16)
            for i, qr_type in enumerate(types):
                card = QRTypeCard(qr_type.type_id, qr_type.icon)
                card.selected.connect(self.type_chosen.emit)
                self._cards.append(card)
                grid.addWidget(card, i // 3, i % 3)
            container_layout.addLayout(grid)

        container_layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

        self.retranslate()

    def retranslate(self) -> None:
        self.header.setText(tr("qrselector.title"))
        for label, category in self._category_labels:
            key = _CATEGORY_KEYS.get(category)
            label.setText(tr(key).upper() if key else category.upper())
        for card in self._cards:
            card.retranslate()
