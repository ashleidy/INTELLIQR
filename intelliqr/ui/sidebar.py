from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Signal

from app.config import APP_NAME, APP_VERSION
from ui.i18n import tr

# Secciones de la barra lateral: (clave de título, [claves de navegación]).
# El título se traduce con "sidebar.group.<clave>"; None = sin título.
_NAV_GROUPS: list[tuple[str | None, list[str]]] = [
    (None, ["home"]),
    ("create", ["qr_create", "barcode"]),
    ("library", ["qr_list", "barcode_list", "history"]),   # ← NUEVO
    ("tools", ["scanner", "print", "settings"]),
]

_NAV_KEYS = [key for _, keys in _NAV_GROUPS for key in keys]


class Sidebar(QFrame):
    navigate = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(248)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        self.logo = QLabel(f"◧  {APP_NAME}")
        self.logo.setObjectName("SidebarLogo")
        layout.addWidget(self.logo)

        self._buttons: dict[str, QPushButton] = {}
        self._group_labels: dict[str, QLabel] = {}

        for group_key, keys in _NAV_GROUPS:
            if group_key is not None:
                title = QLabel(tr(f"sidebar.group.{group_key}").upper())
                title.setObjectName("SidebarSection")
                layout.addWidget(title)
                self._group_labels[group_key] = title
            for key in keys:
                btn = QPushButton(tr(f"nav.{key}"))
                btn.setObjectName("NavButton")
                btn.setCheckable(True)
                btn.setProperty("active", False)
                btn.clicked.connect(lambda checked=False, k=key: self.navigate.emit(k))
                layout.addWidget(btn)
                self._buttons[key] = btn

        layout.addStretch()

        self.footer_label = QLabel(f"{APP_NAME} {APP_VERSION}  ·  {tr('sidebar.free')}")
        self.footer_label.setObjectName("SidebarFooter")
        layout.addWidget(self.footer_label)

        self.set_active("home")

    def set_active(self, key: str) -> None:
        for btn_key, btn in self._buttons.items():
            is_active = btn_key == key
            btn.setChecked(is_active)
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def retranslate(self) -> None:
        for key, btn in self._buttons.items():
            btn.setText(tr(f"nav.{key}"))
        for group_key, label in self._group_labels.items():
            label.setText(tr(f"sidebar.group.{group_key}").upper())
        self.footer_label.setText(f"{APP_NAME} {APP_VERSION}  ·  {tr('sidebar.free')}")