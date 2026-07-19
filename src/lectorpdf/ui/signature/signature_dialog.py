"""Diálogo para obtener el PNG de una firma: dibujarla o reutilizar una guardada."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lectorpdf.ui.signature.biblioteca_firmas import BibliotecaFirmas
from lectorpdf.ui.signature.signature_canvas import SignatureCanvas
from lectorpdf.ui.theme.tokens import PAPEL, TEMA_CLARO

_ROL_ID = int(Qt.ItemDataRole.UserRole)


class SignatureDialog(QDialog):
    def __init__(
        self, parent: QWidget | None = None, biblioteca: BibliotecaFirmas | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Firma")
        self._biblioteca = biblioteca
        self._png: bytes | None = None

        self._canvas = SignatureCanvas()
        self._canvas.setStyleSheet(
            f"background: {PAPEL}; border: 1px solid {TEMA_CLARO.border};"
        )
        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("Nombre para guardar (opcional)")
        self._guardar = QCheckBox("Guardar en la biblioteca")

        limpiar = QPushButton("Limpiar")
        limpiar.clicked.connect(self._canvas.limpiar)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.addButton(limpiar, QDialogButtonBox.ButtonRole.ResetRole)
        botones.accepted.connect(self._aceptar)
        botones.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Dibuja tu firma:"))
        layout.addWidget(self._canvas)
        fila = QHBoxLayout()
        fila.addWidget(self._nombre)
        fila.addWidget(self._guardar)
        layout.addLayout(fila)

        if biblioteca is not None:
            layout.addWidget(QLabel("O reutiliza una firma guardada:"))
            self._lista = QListWidget()
            self._cargar_biblioteca()
            usar = QPushButton("Usar la seleccionada")
            usar.clicked.connect(self._usar_seleccionada)
            layout.addWidget(self._lista)
            layout.addWidget(usar)

        layout.addWidget(botones)

    def png(self) -> bytes | None:
        """PNG elegido (dibujado o de la biblioteca), o None si se canceló."""
        return self._png

    # -- Interno ------------------------------------------------------------

    def _cargar_biblioteca(self) -> None:
        assert self._biblioteca is not None
        for firma in self._biblioteca.listar():
            item = QListWidgetItem(firma.nombre)
            item.setData(_ROL_ID, firma.id)
            self._lista.addItem(item)

    def _aceptar(self) -> None:
        if self._canvas.esta_vacio():
            return  # sin trazo (y sin selección de biblioteca) no se acepta
        png = self._canvas.exportar_png()
        if self._guardar.isChecked() and self._biblioteca is not None:
            nombre = self._nombre.text().strip() or "Firma"
            self._biblioteca.guardar(nombre, png)
        self._png = png
        self.accept()

    def _usar_seleccionada(self) -> None:
        if self._biblioteca is None:
            return
        item = self._lista.currentItem()
        if item is None:
            return
        self._png = self._biblioteca.cargar(str(item.data(_ROL_ID)))
        self.accept()
