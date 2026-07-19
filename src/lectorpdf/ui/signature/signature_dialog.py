"""Diálogo para dibujar una firma y obtener su PNG transparente."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lectorpdf.ui.signature.signature_canvas import SignatureCanvas


class SignatureDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Dibujar firma")
        self._png: bytes | None = None

        self._canvas = SignatureCanvas()
        self._canvas.setStyleSheet("background: white; border: 1px solid #cbd5e1;")

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        limpiar = QPushButton("Limpiar")
        botones.addButton(limpiar, QDialogButtonBox.ButtonRole.ResetRole)
        limpiar.clicked.connect(self._canvas.limpiar)
        botones.accepted.connect(self._aceptar)
        botones.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._canvas)
        layout.addWidget(botones)

    def _aceptar(self) -> None:
        if self._canvas.esta_vacio():
            return  # sin trazo no se acepta
        self._png = self._canvas.exportar_png()
        self.accept()

    def png(self) -> bytes | None:
        """PNG de la firma dibujada, o None si se canceló o no se dibujó."""
        return self._png
