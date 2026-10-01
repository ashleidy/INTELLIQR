"""
Pantalla de Configuración: tamaño de letra e idioma (ES/EN).
Ambos ajustes se guardan en la base de datos local y se aplican al
instante, sin reiniciar la app.
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QApplication
from PySide6.QtCore import Signal

from database.repositories.settings_repository import SettingsRepository
from ui import theme
from ui.i18n import tr, set_language, get_language

_FONT_SIZE_KEYS = ["small", "normal", "large", "xlarge"]


class SettingsScreen(QWidget):
    language_changed = Signal(str)
    font_scale_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings_repo = SettingsRepository()

        layout = QVBoxLayout(self)
        self.title_label = QLabel()
        self.title_label.setObjectName("H1")
        layout.addWidget(self.title_label)

        self.appearance_label = QLabel()
        self.appearance_label.setObjectName("H3")
        layout.addWidget(self.appearance_label)

        font_row = QHBoxLayout()
        self.font_size_label = QLabel()
        font_row.addWidget(self.font_size_label)
        self.font_size_combo = QComboBox()
        self.font_size_combo.currentIndexChanged.connect(self._on_font_size_changed)
        font_row.addWidget(self.font_size_combo)
        font_row.addStretch()
        layout.addLayout(font_row)

        lang_row = QHBoxLayout()
        self.language_label = QLabel()
        lang_row.addWidget(self.language_label)
        self.language_combo = QComboBox()
        self.language_combo.addItem("Español", "es")
        self.language_combo.addItem("English", "en")
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(self.language_combo)
        lang_row.addStretch()
        layout.addLayout(lang_row)

        self.language_note = QLabel()
        self.language_note.setObjectName("Caption")
        self.language_note.setWordWrap(True)
        layout.addWidget(self.language_note)

        layout.addStretch()

        self._load_saved_settings()
        self.retranslate()

    def _load_saved_settings(self) -> None:
        saved_lang = self._settings_repo.get("language", "es")
        set_language(saved_lang)
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentIndex(self.language_combo.findData(saved_lang))
        self.language_combo.blockSignals(False)

        saved_font_key = self._settings_repo.get("font_size", "normal")
        self._font_key = saved_font_key if saved_font_key in _FONT_SIZE_KEYS else "normal"

    def retranslate(self) -> None:
        self.title_label.setText(tr("settings.title"))
        self.appearance_label.setText(tr("settings.appearance"))
        self.font_size_label.setText(tr("settings.font_size"))
        self.language_label.setText(tr("settings.language"))
        self.language_note.setText(tr("settings.language_note"))

        self.font_size_combo.blockSignals(True)
        self.font_size_combo.clear()
        for key in _FONT_SIZE_KEYS:
            self.font_size_combo.addItem(tr(f"settings.font_{key}"), key)
        self.font_size_combo.setCurrentIndex(_FONT_SIZE_KEYS.index(self._font_key))
        self.font_size_combo.blockSignals(False)

    def _on_font_size_changed(self, index: int) -> None:
        key = self.font_size_combo.currentData()
        if not key:
            return
        self._font_key = key
        self._settings_repo.set("font_size", key)
        scale = theme.FONT_SCALE_OPTIONS.get(key, 1.0)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.build_stylesheet(scale))
        self.font_scale_changed.emit(scale)

    def _on_language_changed(self, index: int) -> None:
        lang = self.language_combo.currentData()
        if not lang:
            return
        set_language(lang)
        self._settings_repo.set("language", lang)
        self.retranslate()
        self.language_changed.emit(lang)
