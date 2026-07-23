"""Diálogo para configurar el texto a estampar: contenido, fuente, tamaño, color."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QPlainTextEdit,
    QWidget,
)

from lectorpdf.core.domain.anotaciones import Color, FuenteTexto

_FUENTES = [
    ("Sans", FuenteTexto.SANS),
    ("Serif", FuenteTexto.SERIF),
    ("Monoespaciada", FuenteTexto.MONO),
]

# Colores predefinidos (nombre → RGB 0..1); tinta y acento de la marca.
_COLORES: list[tuple[str, Color]] = [
    ("Negro", (0.07, 0.07, 0.09)),
    ("Rojo (acento)", (0.878, 0.325, 0.290)),
    ("Azul", (0.15, 0.35, 0.70)),
    ("Verde", (0.20, 0.55, 0.30)),
]


class DialogoTexto(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Añadir texto")
        self._texto = QPlainTextEdit()
        self._texto.setPlaceholderText("Escribe el texto…")
        self._fuente = QComboBox()
        for etiqueta, _ in _FUENTES:
            self._fuente.addItem(etiqueta)
        self._tamano = QDoubleSpinBox()
        self._tamano.setRange(4.0, 96.0)
        self._tamano.setValue(12.0)
        self._tamano.setSuffix(" pt")
        self._color = QComboBox()
        for etiqueta, _ in _COLORES:
            self._color.addItem(etiqueta)

        form = QFormLayout(self)
        form.addRow("Texto", self._texto)
        form.addRow("Fuente", self._fuente)
        form.addRow("Tamaño", self._tamano)
        form.addRow("Color", self._color)
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        form.addRow(botones)

    def texto(self) -> str:
        return self._texto.toPlainText().strip()

    def fuente(self) -> FuenteTexto:
        return _FUENTES[self._fuente.currentIndex()][1]

    def tamano(self) -> float:
        return float(self._tamano.value())

    def color(self) -> Color:
        return _COLORES[self._color.currentIndex()][1]
