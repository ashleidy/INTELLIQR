"""Ventana principal: sidebar + área de contenido con QStackedWidget (sección 5, 29)."""
from __future__ import annotations
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLabel
from PySide6.QtCore import Qt

from app.config import APP_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from ui.sidebar import Sidebar
from ui.home import HomeScreen
from ui.qr.qr_wizard import QRWizard
from ui.qr.qr_list import QRListScreen
from ui.barcode.barcode_screen import BarcodeScreen
from ui.barcode.barcode_list import BarcodeListScreen
from ui.history.history_screen import HistoryScreen          
from ui.scanner.scanner_screen import ScannerScreen
from ui.printing.print_screen import PrintScreen
from ui.settings.settings_screen import SettingsScreen


def _placeholder(text: str) -> QWidget:
    label = QLabel(text)
    label.setObjectName("H2")
    label.setAlignment(Qt.AlignCenter)
    return label


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.navigate.connect(self._on_navigate)
        root_layout.addWidget(self.sidebar)

        content_area = QWidget()
        content_area.setObjectName("ContentArea")
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(0)

        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)
        root_layout.addWidget(content_area, 1)

        # --- Pantallas -----------------------------------------------------
        self.home_screen = HomeScreen()
        self.home_screen.create_qr_requested.connect(lambda: self._on_navigate("qr_create"))
        self.home_screen.create_barcode_requested.connect(lambda: self._on_navigate("barcode"))

        self.qr_wizard = QRWizard()
        self.qr_wizard.completed.connect(lambda: self._on_navigate("qr_list"))

        self.qr_list_screen = QRListScreen()
        self.qr_list_screen.open_qr_requested.connect(self._open_qr)

        self.barcode_screen = BarcodeScreen()
        self.barcode_list_screen = BarcodeListScreen()
        self.barcode_list_screen.open_barcode_requested.connect(self._open_barcode)

        self.history_screen = HistoryScreen()   
                   

        self.scanner_screen = ScannerScreen()
        self.print_screen = PrintScreen()
        self.settings_screen = SettingsScreen()
        self.settings_screen.language_changed.connect(self._on_language_changed)

        # --- Registro en el QStackedWidget ---------------------------------
        self._pages: dict[str, QWidget] = {
            "home": self.home_screen,
            "qr_create": self.qr_wizard,
            "qr_list": self.qr_list_screen,
            "barcode": self.barcode_screen,
            "barcode_list": self.barcode_list_screen,
            "history": self.history_screen,                    
            "scanner": self.scanner_screen,
            "print": self.print_screen,
            "settings": self.settings_screen,
        }
        for page in self._pages.values():
            self.content_stack.addWidget(page)

        self._on_navigate("home")

    def _on_navigate(self, key: str) -> None:
        self.sidebar.set_active(key if key in self._pages else "home")
        page = self._pages.get(key, self.home_screen)
        if key == "qr_create":
            self.qr_wizard.reset()
        if key == "barcode":
            self.barcode_screen.reset()
        if key == "qr_list":
            self.qr_list_screen.refresh()
        if key == "barcode_list":
            self.barcode_list_screen.refresh()
        if key == "history":                                   
            self.history_screen.refresh()
        if key == "print":
            self.print_screen.refresh()
        self.content_stack.setCurrentWidget(page)

    def _open_qr(self, qr_id: int) -> None:
        """Abre un QR ya guardado (desde Mis QR) directamente en el paso de
        exportación del asistente, con opción de volver atrás a editar."""
        self.sidebar.set_active("qr_create")
        self.content_stack.setCurrentWidget(self.qr_wizard)
        self.qr_wizard.open_existing(qr_id)

    def _open_barcode(self, barcode_id: int) -> None:
        """Abre un código de barras ya guardado (desde Mis códigos de barra)
        para verlo o editarlo."""
        self.sidebar.set_active("barcode")
        self.content_stack.setCurrentWidget(self.barcode_screen)
        self.barcode_screen.open_existing(barcode_id)

    def _on_language_changed(self, lang: str) -> None:
        """Actualiza al instante los textos de toda la app."""
        self.sidebar.retranslate()
        self.home_screen.retranslate()
        self.qr_wizard.retranslate()
        self.qr_list_screen.retranslate()
        self.barcode_screen.retranslate()
        self.barcode_list_screen.retranslate()
        self.history_screen.retranslate()                      
        self.scanner_screen.retranslate()
        self.print_screen.retranslate()