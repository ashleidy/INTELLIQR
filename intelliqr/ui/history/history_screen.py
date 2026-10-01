from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QScrollArea, QMessageBox, QApplication,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices

from io import BytesIO
from PIL import Image

from core.scan_engine.scanner import classify_action
from database.repositories.scan_repository import ScanRepository
from ui.common.image_viewer import show_image_viewer, save_image_with_dialog
from ui.i18n import tr


class HistoryScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._repo = ScanRepository()

        root = QVBoxLayout(self)
        root.setSpacing(14)

        self.title_label = QLabel()
        self.title_label.setObjectName("H1")
        root.addWidget(self.title_label)

        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self._refresh)
        root.addWidget(self.search_input)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        scroll.setWidget(self.list_container)
        root.addWidget(scroll, 1)

        self.retranslate()

    # ---------------- API pública ----------------
    def refresh(self) -> None:
        self._refresh()

    def retranslate(self) -> None:
        self.title_label.setText(tr("history.title"))
        self.search_input.setPlaceholderText(tr("history.search"))
        self._refresh()

    # ---------------- Interno ----------------
    def _clear(self) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _refresh(self) -> None:
        self._clear()
        query = self.search_input.text().strip().lower()
        records = self._repo.list_all() if hasattr(self._repo, "list_all") else []

        if query:
            records = [r for r in records if query in (r.content or "").lower()]

        if not records:
            empty = QLabel(tr("history.empty"))
            empty.setObjectName("Caption")
            self.list_layout.insertWidget(0, empty)
            return

        for idx, rec in enumerate(records):
            self.list_layout.insertWidget(idx, self._make_row(rec))

    def _make_row(self, rec) -> QFrame:
        row = QFrame()
        row.setObjectName("Card")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Miniatura del QR/código escaneado, si el registro tiene imagen guardada.
        pil_image = self._record_pil_image(rec)
        thumb = QLabel()
        thumb.setFixedSize(72, 72)
        thumb.setAlignment(Qt.AlignCenter)
        pix = self._record_thumbnail(rec)
        if pix is not None:
            thumb.setPixmap(pix)
            thumb.setCursor(Qt.PointingHandCursor)
            thumb.setToolTip(tr("scanhistory.view"))
            thumb.mousePressEvent = lambda _e, img=pil_image, r=rec: self._on_view(img, r)
            thumb.setStyleSheet("background-color: #F1F5F9; border-radius: 8px;")
        else:
            # Sin imagen guardada (registros antiguos, o vino de un origen sin
            # foto): dejamos un icono neutro en vez de un hueco en blanco.
            thumb.setText("🔗")
            thumb.setToolTip(tr("scanhistory.no_image_tip"))
            thumb.setStyleSheet(
                "background-color: #F1F5F9; border-radius: 8px; font-size: 22px;"
            )
        layout.addWidget(thumb)

        # Texto: tipo, enlace/contenido y fecha.
        col = QVBoxLayout()
        type_label = QLabel(rec.type_label)
        type_label.setObjectName("H3")
        content_label = QLabel(rec.content)
        content_label.setWordWrap(True)
        date_label = QLabel(
            f"{tr('history.created_prefix')}: {rec.created_at.strftime('%d/%m/%Y %H:%M')}"
            if getattr(rec, "created_at", None) else ""
        )
        date_label.setObjectName("Caption")
        col.addWidget(type_label)
        col.addWidget(content_label)
        col.addWidget(date_label)
        layout.addLayout(col, 1)

        # Botones: Abrir · Copiar · Eliminar (mismo trío de avisos que usa
        # la pantalla de código de barras: aviso si falla, sin aviso si sale bien).
        openable_url = classify_action(rec.content)

        open_btn = QPushButton(tr("history.open"))
        open_btn.setObjectName("SecondaryButton")
        if openable_url:
            open_btn.clicked.connect(lambda _=False, u=openable_url: self._on_open(u))
        else:
            open_btn.setEnabled(False)
            open_btn.setToolTip(tr("history.open_unavailable_tip"))
        layout.addWidget(open_btn)

        view_btn = QPushButton(tr("scanhistory.view"))
        view_btn.setObjectName("SecondaryButton")
        download_btn = QPushButton(tr("scanhistory.download"))
        download_btn.setObjectName("SecondaryButton")
        if pil_image is not None:
            view_btn.clicked.connect(lambda _=False, img=pil_image, r=rec: self._on_view(img, r))
            download_btn.clicked.connect(lambda _=False, img=pil_image, r=rec: self._on_download(img, r))
        else:
            view_btn.setEnabled(False)
            download_btn.setEnabled(False)
            view_btn.setToolTip(tr("scanhistory.no_image_tip"))
            download_btn.setToolTip(tr("scanhistory.no_image_tip"))
        layout.addWidget(view_btn)
        layout.addWidget(download_btn)

        copy_btn = QPushButton(tr("history.copy"))
        copy_btn.setObjectName("SecondaryButton")
        copy_btn.clicked.connect(
            lambda _=False, c=rec.content: QApplication.clipboard().setText(c)
        )
        layout.addWidget(copy_btn)

        del_btn = QPushButton(tr("history.delete"))
        del_btn.setObjectName("SecondaryButton")
        del_btn.clicked.connect(lambda _=False, r=rec: self._on_delete(r))
        layout.addWidget(del_btn)

        return row

    def _record_pil_image(self, rec) -> Image.Image | None:
        blob = getattr(rec, "image", None)
        if not blob:
            return None
        try:
            return Image.open(BytesIO(blob)).convert("RGB")
        except Exception:
            return None

    def _on_view(self, pil_image: Image.Image | None, rec) -> None:
        if pil_image is None:
            return
        show_image_viewer(self, pil_image, suggested_name=rec.type_label)

    def _on_download(self, pil_image: Image.Image | None, rec) -> None:
        if pil_image is None:
            return
        save_image_with_dialog(self, pil_image, suggested_name=rec.type_label)

    def _record_thumbnail(self, rec) -> QPixmap | None:
        """Si el repo guarda la imagen del QR, la convertimos a QPixmap."""
        blob = getattr(rec, "image", None)
        if not blob:
            return None
        try:
            from io import BytesIO
            from PIL import Image
            img = Image.open(BytesIO(blob)).convert("RGB")
            data = img.tobytes("raw", "RGB")
            from PySide6.QtGui import QImage
            qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
            return QPixmap.fromImage(qimg.copy()).scaled(
                68, 68, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        except Exception:
            return None

    def _on_open(self, url: str) -> None:
        # Igual que en el paso de exportar/imprimir: si algo falla, avisamos
        # con QMessageBox en vez de fallar en silencio.
        try:
            opened = QDesktopServices.openUrl(QUrl(url))
        except Exception:
            opened = False
        if not opened:
            QMessageBox.warning(self, tr("history.open_fail_title"), tr("history.open_fail_msg"))

    def _on_delete(self, rec) -> None:
        confirm = QMessageBox.question(
            self,
            tr("history.delete_confirm_title"),
            tr("history.delete_confirm_msg"),
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            if hasattr(self._repo, "delete"):
                self._repo.delete(rec.id)
        except Exception:
            QMessageBox.warning(self, tr("history.delete_fail_title"), tr("history.delete_fail_msg"))
            return
        self._refresh()
