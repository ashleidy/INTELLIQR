"""
Paso 2 del flujo de creación: diseño y personalización (secciones 13-15).
Estructura de pestañas: Marco / Forma / Logo, con miniaturas generadas por
el propio QRGenerator (no iconos genéricos), igual que el flujo de referencia.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox,
    QCheckBox, QPushButton, QScrollArea, QFrame, QFileDialog, QColorDialog,
    QSlider, QButtonGroup, QTabWidget
)
from PySide6.QtCore import Signal, QTimer, Qt, QSize
from PySide6.QtGui import QColor, QPixmap, QImage

from core.qr_engine.generator import QRGenerator, QRDesignOptions
from core.qr_engine.designer import FrameOptions, apply_frame
from core.qr_engine.validator import check_logo_ratio
from ui.qr.qr_preview import QRPreviewWidget, pil_to_qpixmap
from ui import theme
from ui.i18n import tr

_SAMPLE_PAYLOAD = "https://intelliqr.app"

_PATTERNS = ["cuadrado", "redondeado", "puntos", "suave", "moderno"]
_FRAMES = ["ninguno", "simple", "redondeado", "moderno", "etiqueta", "promocional",
           "circular", "telefono", "navegador", "bolsa"]
_FONTS = ["Sans-Serif", "Segoe UI", "Arial", "Georgia", "Courier New"]


def _pil_to_pixmap(pil_image, size: int) -> QPixmap:
    pixmap = pil_to_qpixmap(pil_image)
    return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class _ColorRow(QWidget):
    """Fila 'Color de X': etiqueta arriba, input hex + swatch abajo (como en la referencia)."""
    changed = Signal()

    def __init__(self, label_key: str, default_hex: str, parent=None):
        super().__init__(parent)
        self._label_key = label_key
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.label_widget = QLabel(tr(label_key))
        layout.addWidget(self.label_widget)

        row = QHBoxLayout()
        self.hex_input = QLineEdit(default_hex)
        self.hex_input.textChanged.connect(self._on_text_changed)
        self.swatch_btn = QPushButton()
        self.swatch_btn.setFixedSize(48, 36)
        self.swatch_btn.setCursor(Qt.PointingHandCursor)
        self.swatch_btn.clicked.connect(self._pick_color)
        row.addWidget(self.hex_input, 1)
        row.addWidget(self.swatch_btn)
        layout.addLayout(row)
        self._update_swatch()

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.hex_input.text() or "#FFFFFF"), self)
        if color.isValid():
            self.hex_input.setText(color.name().upper())

    def _on_text_changed(self) -> None:
        self._update_swatch()
        self.changed.emit()

    def _update_swatch(self) -> None:
        color = self.hex_input.text() or "#FFFFFF"
        self.swatch_btn.setStyleSheet(
            f"background-color: {color}; border: 1px solid {theme.BORDER}; border-radius: 6px;"
        )

    def value(self) -> str:
        return self.hex_input.text() or "#FFFFFF"

    def set_value(self, value: str) -> None:
        self.hex_input.setText(value)

    def retranslate(self) -> None:
        self.label_widget.setText(tr(self._label_key))


class _ToggleRow(QWidget):
    """Interruptor tipo 'Fondo transparente' / 'Degradado'."""
    changed = Signal()

    def __init__(self, label_key: str, parent=None):
        super().__init__(parent)
        self._label_key = label_key
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.checkbox = QCheckBox(tr(label_key))
        # stateChanged envía el nuevo estado (int) como argumento; nuestra
        # señal `changed` no recibe argumentos. Conectarlos directo
        # (stateChanged.connect(self.changed.emit)) lanza un TypeError que
        # PySide6 traga en silencio, así que la casilla se marcaba en
        # pantalla pero el resto de la app nunca se enteraba del cambio
        # (el panel de colores no aparecía y la vista previa no se
        # actualizaba). Por eso pasa por un lambda que ignora el argumento.
        self.checkbox.stateChanged.connect(lambda _state: self.changed.emit())
        layout.addWidget(self.checkbox)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_checked(self, value: bool) -> None:
        self.checkbox.setChecked(value)

    def retranslate(self) -> None:
        self.checkbox.setText(tr(self._label_key))


class _ThumbnailStrip(QScrollArea):
    """Fila horizontal desplazable de miniaturas seleccionables (patrones o marcos)."""
    selection_changed = Signal(str)

    def __init__(self, translation_prefix: str, parent=None):
        super().__init__(parent)
        self._translation_prefix = translation_prefix
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedHeight(120)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        self._layout = QHBoxLayout(container)
        self._layout.setSpacing(10)
        self.setWidget(container)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.group.buttonClicked.connect(self._on_clicked)

    def add_item(self, item_id: str, pixmap: QPixmap) -> None:
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setFixedSize(96, 100)
        btn.setIcon(pixmap)
        btn.setIconSize(QSize(64, 64))
        btn.setText(f"\n{tr(f'{self._translation_prefix}.{item_id}')}")
        btn.setProperty("item_id", item_id)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border: 2px solid {theme.BORDER};
                border-radius: 8px;
                color: {theme.TEXT_SECONDARY};
                font-size: 10px;
                padding-top: 6px;
            }}
            QPushButton:checked {{
                border-color: {theme.PRIMARY};
                background-color: {theme.PRIMARY_VERY_LIGHT};
                color: {theme.PRIMARY_DARK};
            }}
            QPushButton:hover {{ border-color: {theme.PRIMARY_LIGHT}; }}
        """)
        self.group.addButton(btn)
        self._layout.addWidget(btn)

    def finish(self) -> None:
        self._layout.addStretch()

    def retranslate(self) -> None:
        for btn in self.group.buttons():
            item_id = btn.property("item_id")
            btn.setText(f"\n{tr(f'{self._translation_prefix}.{item_id}')}")

    def _on_clicked(self, btn) -> None:
        self.selection_changed.emit(btn.property("item_id"))

    def set_selected(self, item_id: str) -> None:
        for btn in self.group.buttons():
            if btn.property("item_id") == item_id:
                btn.setChecked(True)
                return

    def selected_id(self) -> str | None:
        checked = self.group.checkedButton()
        return checked.property("item_id") if checked else None


class QRDesignStep(QWidget):
    """Emite `design_ready(design_options_dict, frame_options_dict)`."""
    design_ready = Signal(dict, dict)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._payload: str = _SAMPLE_PAYLOAD
        self._generator = QRGenerator()
        self._logo_path: str | None = None

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(self._update_preview)

        root = QHBoxLayout(self)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left = QWidget()
        left_layout = QVBoxLayout(left)

        self.title_label = QLabel()
        self.title_label.setObjectName("H2")
        left_layout.addWidget(self.title_label)

        self.tabs = QTabWidget()
        left_layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_frame_tab(), "")
        self.tabs.addTab(self._build_shape_tab(), "")
        self.tabs.addTab(self._build_logo_tab(), "")

        nav_row = QHBoxLayout()
        self.back_btn = QPushButton()
        self.back_btn.setObjectName("SecondaryButton")
        self.back_btn.clicked.connect(self.back_requested.emit)
        self.continue_btn = QPushButton()
        self.continue_btn.setObjectName("PrimaryButton")
        self.continue_btn.clicked.connect(self._on_continue)
        nav_row.addWidget(self.back_btn)
        nav_row.addStretch()
        nav_row.addWidget(self.continue_btn)
        left_layout.addLayout(nav_row)

        left_scroll.setWidget(left)
        root.addWidget(left_scroll, 3)

        right = QVBoxLayout()
        self.preview = QRPreviewWidget()
        right.addWidget(self.preview)
        right.addStretch()
        root.addLayout(right, 2)

        self._populate_frame_thumbnails()
        self._populate_shape_thumbnails()
        self.retranslate()

    def retranslate(self) -> None:
        self.title_label.setText(tr("qrdesign.title"))
        self.tabs.setTabText(0, tr("qrdesign.tab.frame"))
        self.tabs.setTabText(1, tr("qrdesign.tab.shape"))
        self.tabs.setTabText(2, tr("qrdesign.tab.logo"))
        self.back_btn.setText(tr("qrdesign.back"))
        self.continue_btn.setText(tr("qrdesign.continue"))

        self.frame_phrase_label.setText(tr("qrdesign.frame.phrase"))
        self.frame_font_label.setText(tr("qrdesign.frame.font"))
        self.frame_color_row.retranslate()
        self.frame_text_color_row.retranslate()
        self.frame_strip.retranslate()

        self.shape_title_label.setText(tr("qrdesign.shape.title"))
        self.shape_style_label.setText(tr("qrdesign.shape.style"))
        self.bg_color_row.retranslate()
        self.fg_color_row.retranslate()
        self.transparent_toggle.retranslate()
        self.gradient_toggle.retranslate()
        self.gradient_start_row.retranslate()
        self.gradient_end_row.retranslate()
        self.shape_strip.retranslate()
        self.image_size_label.setText(tr("qrdesign.shape.image_size"))

        self.logo_title_label.setText(tr("qrdesign.logo.title"))
        if not self._logo_path:
            self.logo_preview.setText(tr("qrdesign.logo.none_selected"))
        self.upload_logo_btn.setText(tr("qrdesign.logo.upload"))
        self.remove_logo_btn.setText(tr("qrdesign.logo.remove"))
        self.logo_size_label.setText(tr("qrdesign.logo.size"))

    # ---------- Pestaña MARCO ----------
    def _build_frame_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.frame_strip = _ThumbnailStrip("frame")
        self.frame_strip.selection_changed.connect(self._on_changed)
        layout.addWidget(self.frame_strip)

        fields_row = QHBoxLayout()

        phrase_col = QVBoxLayout()
        self.frame_phrase_label = QLabel()
        phrase_col.addWidget(self.frame_phrase_label)
        self.frame_text_input = QLineEdit("ESCANÉAME")
        self.frame_text_input.textChanged.connect(self._on_changed)
        phrase_col.addWidget(self.frame_text_input)
        fields_row.addLayout(phrase_col, 1)

        font_col = QVBoxLayout()
        self.frame_font_label = QLabel()
        font_col.addWidget(self.frame_font_label)
        self.frame_font_combo = QComboBox()
        self.frame_font_combo.addItems(_FONTS)
        self.frame_font_combo.currentTextChanged.connect(self._on_changed)
        font_col.addWidget(self.frame_font_combo)
        fields_row.addLayout(font_col, 1)

        layout.addLayout(fields_row)

        self.frame_color_row = _ColorRow("qrdesign.frame.color", "#2563EB")
        self.frame_color_row.changed.connect(self._on_changed)
        layout.addWidget(self.frame_color_row)

        self.frame_text_color_row = _ColorRow("qrdesign.frame.text_color", "#FFFFFF")
        self.frame_text_color_row.changed.connect(self._on_changed)
        layout.addWidget(self.frame_text_color_row)

        layout.addStretch()
        return tab

    def _populate_frame_thumbnails(self) -> None:
        base_result = self._generator.generate(_SAMPLE_PAYLOAD, QRDesignOptions(box_size=4, border=1))
        for style_id in _FRAMES:
            frame_opts = FrameOptions(style=style_id, text="SCAN ME", frame_color="#000000",
                                       text_color="#FFFFFF", font_size=12, padding=8)
            framed = apply_frame(base_result.image, frame_opts)
            pixmap = _pil_to_pixmap(framed, 64)
            self.frame_strip.add_item(style_id, pixmap)
        self.frame_strip.finish()
        self.frame_strip.set_selected("ninguno")

    # ---------- Pestaña FORMA ----------
    def _build_shape_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.shape_title_label = QLabel()
        self.shape_title_label.setObjectName("H3")
        layout.addWidget(self.shape_title_label)
        self.shape_style_label = QLabel()
        layout.addWidget(self.shape_style_label)

        self.shape_strip = _ThumbnailStrip("pattern")
        self.shape_strip.selection_changed.connect(self._on_changed)
        layout.addWidget(self.shape_strip)

        colors_row = QHBoxLayout()
        self.bg_color_row = _ColorRow("qrdesign.shape.bg_color", "#FFFFFF")
        self.fg_color_row = _ColorRow("qrdesign.shape.fg_color", "#0F172A")
        self.bg_color_row.changed.connect(self._on_changed)
        self.fg_color_row.changed.connect(self._on_changed)
        colors_row.addWidget(self.bg_color_row)
        colors_row.addWidget(self.fg_color_row)
        layout.addLayout(colors_row)

        toggles_row = QHBoxLayout()
        self.transparent_toggle = _ToggleRow("qrdesign.shape.transparent")
        self.transparent_toggle.changed.connect(self._on_changed)
        self.gradient_toggle = _ToggleRow("qrdesign.shape.gradient")
        self.gradient_toggle.changed.connect(self._on_gradient_toggled)
        toggles_row.addWidget(self.transparent_toggle)
        toggles_row.addWidget(self.gradient_toggle)
        layout.addLayout(toggles_row)

        self.gradient_options_widget = QWidget()
        gradient_layout = QHBoxLayout(self.gradient_options_widget)
        gradient_layout.setContentsMargins(0, 0, 0, 0)
        self.gradient_start_row = _ColorRow("qrdesign.shape.gradient_start", "#2563EB")
        self.gradient_end_row = _ColorRow("qrdesign.shape.gradient_end", "#60A5FA")
        self.gradient_start_row.changed.connect(self._on_changed)
        self.gradient_end_row.changed.connect(self._on_changed)
        gradient_layout.addWidget(self.gradient_start_row)
        gradient_layout.addWidget(self.gradient_end_row)
        self.gradient_direction_combo = QComboBox()
        self.gradient_direction_combo.addItems(["horizontal", "vertical"])
        self.gradient_direction_combo.currentTextChanged.connect(self._on_changed)
        gradient_layout.addWidget(self.gradient_direction_combo)
        self.gradient_options_widget.setVisible(False)
        layout.addWidget(self.gradient_options_widget)

        self.image_size_label = QLabel()
        layout.addWidget(self.image_size_label)
        self.image_size_slider = QSlider(Qt.Horizontal)
        self.image_size_slider.setRange(4, 20)
        self.image_size_slider.setValue(10)
        self.image_size_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self.image_size_slider)

        layout.addStretch()
        return tab

    def _populate_shape_thumbnails(self) -> None:
        for pattern_id in _PATTERNS:
            result = self._generator.generate(
                _SAMPLE_PAYLOAD,
                QRDesignOptions(pattern=pattern_id, box_size=4, border=1, fg_color="#000000", bg_color="#FFFFFF"),
            )
            pixmap = _pil_to_pixmap(result.image, 64)
            self.shape_strip.add_item(pattern_id, pixmap)
        self.shape_strip.finish()
        self.shape_strip.set_selected("cuadrado")

    def _on_gradient_toggled(self) -> None:
        self.gradient_options_widget.setVisible(self.gradient_toggle.is_checked())
        self._on_changed()

    # ---------- Pestaña LOGO ----------
    def _build_logo_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.logo_title_label = QLabel()
        self.logo_title_label.setObjectName("H3")
        layout.addWidget(self.logo_title_label)

        self.logo_preview = QLabel()
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setFixedHeight(100)
        self.logo_preview.setStyleSheet(
            f"border: 2px dashed {theme.BORDER}; border-radius: 8px; color: {theme.TEXT_SECONDARY};"
        )
        layout.addWidget(self.logo_preview)

        buttons_row = QHBoxLayout()
        self.upload_logo_btn = QPushButton()
        self.upload_logo_btn.setObjectName("PrimaryButton")
        self.upload_logo_btn.clicked.connect(self._pick_logo)
        self.remove_logo_btn = QPushButton()
        self.remove_logo_btn.setObjectName("SecondaryButton")
        self.remove_logo_btn.setEnabled(False)
        self.remove_logo_btn.clicked.connect(self._remove_logo)
        buttons_row.addWidget(self.upload_logo_btn)
        buttons_row.addWidget(self.remove_logo_btn)
        buttons_row.addStretch()
        layout.addLayout(buttons_row)

        self.logo_size_label = QLabel()
        layout.addWidget(self.logo_size_label)
        self.logo_size_slider = QSlider(Qt.Horizontal)
        self.logo_size_slider.setRange(10, 35)
        self.logo_size_slider.setValue(22)
        self.logo_size_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self.logo_size_slider)

        self.logo_warning_label = QLabel("")
        self.logo_warning_label.setObjectName("ErrorLabel")
        self.logo_warning_label.hide()
        layout.addWidget(self.logo_warning_label)

        layout.addStretch()
        return tab

    def _pick_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo", "", "Imágenes (*.png *.jpg *.jpeg *.svg)")
        if path:
            self._logo_path = path
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.logo_preview.setPixmap(pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.logo_preview.setText("")
            self.remove_logo_btn.setEnabled(True)
            self._on_changed()

    def _remove_logo(self) -> None:
        self._logo_path = None
        self.logo_preview.setText(tr("qrdesign.logo.none_selected"))
        self.logo_preview.setPixmap(QPixmap())
        self.remove_logo_btn.setEnabled(False)
        self._on_changed()

    # ---------- Utilidades comunes ----------
    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("H3")
        return label

    def load_payload(self, payload: str, previous_design: dict | None = None) -> None:
        self._payload = payload
        if previous_design:
            self._apply_previous(previous_design)
        self._update_preview()

    def _apply_previous(self, d: dict) -> None:
        self.shape_strip.set_selected(d.get("pattern", "cuadrado"))
        self.bg_color_row.set_value(d.get("bg_color", "#FFFFFF"))
        self.fg_color_row.set_value(d.get("fg_color", "#0F172A"))
        self.transparent_toggle.set_checked(d.get("transparent_background", False))
        self.gradient_toggle.set_checked(d.get("gradient_enabled", False))
        self.gradient_start_row.set_value(d.get("gradient_start", "#2563EB"))
        self.gradient_end_row.set_value(d.get("gradient_end", "#60A5FA"))
        self.gradient_options_widget.setVisible(d.get("gradient_enabled", False))
        self._logo_path = d.get("logo_path")
        self.logo_size_slider.setValue(int(d.get("logo_size_ratio", 0.22) * 100))
        self.image_size_slider.setValue(int(d.get("box_size", 10)))

    def _on_changed(self, *args) -> None:
        self._debounce.start()

    def _build_design_options(self) -> QRDesignOptions:
        ratio = self.logo_size_slider.value() / 100
        return QRDesignOptions(
            pattern=self.shape_strip.selected_id() or "cuadrado",
            corner_style="cuadradas",
            fg_color=self.fg_color_row.value(),
            bg_color=self.bg_color_row.value(),
            gradient_enabled=self.gradient_toggle.is_checked(),
            gradient_start=self.gradient_start_row.value(),
            gradient_end=self.gradient_end_row.value(),
            gradient_direction=self.gradient_direction_combo.currentText(),
            logo_path=self._logo_path,
            logo_size_ratio=ratio,
            transparent_background=self.transparent_toggle.is_checked(),
            box_size=self.image_size_slider.value(),
        )

    def _build_frame_options(self) -> FrameOptions:
        return FrameOptions(
            style=self.frame_strip.selected_id() or "ninguno",
            text=self.frame_text_input.text() or "ESCANÉAME",
            text_color=self.frame_text_color_row.value(),
            frame_color=self.frame_color_row.value(),
        )

    def _update_preview(self) -> None:
        if not self._payload:
            return
        design = self._build_design_options()
        warning = check_logo_ratio(design.logo_size_ratio)
        self.logo_warning_label.setText(warning or "")
        self.logo_warning_label.setVisible(bool(warning))
        try:
            result = self._generator.generate(self._payload, design)
            frame = self._build_frame_options()
            final_image = apply_frame(result.image, frame)
            self.preview.show_image(final_image, result.warnings)
        except Exception:
            self.preview.show_placeholder("No pudimos generar el código. Revisa la personalización.")

    def _on_continue(self) -> None:
        design = self._build_design_options()
        frame = self._build_frame_options()
        design_dict = {
            "pattern": design.pattern, "corner_style": design.corner_style,
            "fg_color": design.fg_color, "bg_color": design.bg_color,
            "gradient_enabled": design.gradient_enabled, "gradient_start": design.gradient_start,
            "gradient_end": design.gradient_end, "gradient_direction": design.gradient_direction,
            "logo_path": design.logo_path, "logo_size_ratio": design.logo_size_ratio,
            "transparent_background": design.transparent_background,
            "box_size": design.box_size,
        }
        frame_dict = {
            "style": frame.style, "text": frame.text,
            "frame_color": frame.frame_color, "frame_text_color": frame.text_color,
        }
        self.design_ready.emit(design_dict, frame_dict)
