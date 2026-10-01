"""Diálogo de vista ampliada para imágenes escaneadas (QR/código de barras).

Compartido entre 'Resultado del escáner' e 'Historial de escaneos' para que
ambos se comporten igual: clic en la miniatura -> ver en grande -> descargar,
con los mismos avisos de error que usa el resto de la app al exportar.
"""
from __future__ import annotations
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PIL import Image

from app.config import EXPORTS_DIR
from ui.qr.qr_preview import pil_to_qpixmap
from ui.i18n import tr


def _safe_filename(text: str, fallback: str = "escaneo") -> str:
    import re
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", text).strip().strip(".")
    return safe or fallback


def save_image_with_dialog(parent, image: Image.Image, suggested_name: str = "escaneo") -> bool:
    """Abre el diálogo 'Guardar como' y exporta la imagen a PNG.

    Devuelve True si se guardó, False si el usuario canceló. En caso de
    error, avisa con QMessageBox igual que hacen el resto de exportaciones
    de la app (QR, código de barras).
    """
    default_path = str(EXPORTS_DIR / f"{_safe_filename(suggested_name)}.png")
    path, _ = QFileDialog.getSaveFileName(
        parent, tr("scanhistory.download_dialog_title"), default_path, "PNG (*.png)"
    )
    if not path:
        return False
    try:
        image.convert("RGB").save(path, format="PNG")
        QMessageBox.information(
            parent, tr("scanhistory.download_done_title"), tr("scanhistory.download_done_msg")
        )
        return True
    except Exception:
        QMessageBox.warning(
            parent, tr("scanhistory.download_fail_title"), tr("scanhistory.download_fail_msg")
        )
        return False


class ImageViewerDialog(QDialog):
    """Ventana simple con la imagen a tamaño grande y un botón para descargarla."""

    def __init__(self, image: Image.Image, suggested_name: str = "escaneo", parent=None):
        super().__init__(parent)
        self._image = image
        self._suggested_name = suggested_name
        self.setWindowTitle(tr("scanhistory.view_title"))
        self.setMinimumSize(420, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        pixmap = pil_to_qpixmap(image)
        side = min(380, max(pixmap.width(), pixmap.height()))
        image_label.setPixmap(
            pixmap.scaled(side, side, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        layout.addWidget(image_label, 1)

        buttons_row = QHBoxLayout()
        download_btn = QPushButton(tr("scanhistory.download"))
        download_btn.setObjectName("PrimaryButton")
        download_btn.clicked.connect(self._on_download)
        close_btn = QPushButton(tr("scanhistory.close"))
        close_btn.setObjectName("SecondaryButton")
        close_btn.clicked.connect(self.reject)
        buttons_row.addStretch()
        buttons_row.addWidget(close_btn)
        buttons_row.addWidget(download_btn)
        layout.addLayout(buttons_row)

    def _on_download(self) -> None:
        save_image_with_dialog(self, self._image, self._suggested_name)


def show_image_viewer(parent, image: Image.Image, suggested_name: str = "escaneo") -> None:
    ImageViewerDialog(image, suggested_name, parent).exec()
