"""Widget de previsualización en tiempo real del QR (sección 12 y 16)."""
from __future__ import annotations
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from PIL import Image

from ui import theme
from ui.i18n import tr


def pil_to_qimage(pil_image: Image.Image) -> QImage:
    """Igual que pil_to_qpixmap, pero devolviendo un QImage independiente."""
    img = pil_image.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    return QImage(data, img.width, img.height, img.width * 4, QImage.Format_RGBA8888).copy()


def pil_to_qpixmap(pil_image: Image.Image) -> QPixmap:
    """Convierte una imagen PIL a QPixmap copiando los bytes.

    Se evita a propósito PIL.ImageQt: ese objeto envuelve el búfer de la
    imagen sin copiarlo y, si Python lo recolecta antes de tiempo, Qt sigue
    leyendo memoria ya liberada y la aplicación se cierra de golpe.
    """
    img = pil_image.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qimage = QImage(data, img.width, img.height, img.width * 4, QImage.Format_RGBA8888)
    # .copy() fuerza a Qt a quedarse con sus propios bytes.
    return QPixmap.fromImage(qimage.copy())


class QRPreviewWidget(QFrame):
    """Panel con fondo claro y el QR centrado, que se adapta al tamaño disponible."""

    MIN_IMAGE = 300

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreviewPanel")
        self.setMinimumSize(360, 460)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._pixmap: QPixmap | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.title_label = QLabel(tr("qrpreview.title"))
        self.title_label.setObjectName("H3")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("background: transparent;")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(self.MIN_IMAGE, self.MIN_IMAGE)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setWordWrap(True)
        self.image_label.setStyleSheet(
            f"background-color: {theme.SURFACE}; border: 1px solid {theme.BORDER};"
            f" border-radius: {theme.RADIUS_MD}px; padding: 10px;"
        )

        self.hint_label = QLabel(tr("qrpreview.hint"))
        self.hint_label.setObjectName("Caption")
        self.hint_label.setWordWrap(True)
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet("background: transparent;")

        self.warning_label = QLabel("")
        self.warning_label.setObjectName("ErrorLabel")
        self.warning_label.setWordWrap(True)
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setStyleSheet("background: transparent;")
        self.warning_label.hide()

        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label, 1)
        layout.addWidget(self.hint_label)
        layout.addWidget(self.warning_label)

    # ---- API pública ----
    def show_placeholder(self, message: str | None = None) -> None:
        self._pixmap = None
        self.image_label.clear()
        self.image_label.setText(message or tr("qrpreview.placeholder"))
        self.warning_label.hide()

    def show_image(self, pil_image: Image.Image, warnings: list[str] | None = None) -> None:
        self._pixmap = pil_to_qpixmap(pil_image)
        self.image_label.setText("")
        self._rescale()
        if warnings:
            self.warning_label.setText(" ".join(warnings))
            self.warning_label.show()
        else:
            self.warning_label.hide()

    def retranslate(self) -> None:
        self.title_label.setText(tr("qrpreview.title"))
        self.hint_label.setText(tr("qrpreview.hint"))
        if self._pixmap is None and self.image_label.text():
            self.image_label.setText(tr("qrpreview.placeholder"))

    # ---- Escalado adaptable ----
    def resizeEvent(self, event) -> None:  # noqa: N802 (API de Qt)
        super().resizeEvent(event)
        self._rescale()

    def _rescale(self) -> None:
        if self._pixmap is None:
            return
        area = self.image_label.size()
        side = max(self.MIN_IMAGE, min(area.width() - 24, area.height() - 24))
        # Al ampliar usamos interpolación dura: un QR son cuadrados, así que
        # queda nítido en vez de borroso. Al reducir, suavizada.
        mode = Qt.FastTransformation if side > self._pixmap.width() else Qt.SmoothTransformation
        self.image_label.setPixmap(self._pixmap.scaled(side, side, Qt.KeepAspectRatio, mode))
