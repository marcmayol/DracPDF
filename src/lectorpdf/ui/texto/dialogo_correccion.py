"""Diálogo de corrección de texto: muestra el original, pide la sustitución y
avisa de los límites (fuente sustituta distinta, sin reflujo)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QWidget,
)

from lectorpdf.core.domain.anotaciones import FuenteTexto

_FUENTES = [
    ("Serif", FuenteTexto.SERIF),
    ("Sans", FuenteTexto.SANS),
    ("Monoespaciada", FuenteTexto.MONO),
]

_AVISO = (
    "La fuente sustituta puede diferir de la original y la corrección no reajusta "
    "el párrafo (sin reflujo). El texto original se elimina del documento."
)


class DialogoCorreccion(QDialog):
    def __init__(self, original: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Corregir texto")
        orig = QLabel(original or "(selección)")
        orig.setWordWrap(True)
        self._nuevo = QLineEdit(original)
        self._fuente = QComboBox()
        for etiqueta, _ in _FUENTES:
            self._fuente.addItem(etiqueta)
        aviso = QLabel(_AVISO)
        aviso.setObjectName("pistaVacio")
        aviso.setWordWrap(True)

        form = QFormLayout(self)
        form.addRow("Original", orig)
        form.addRow("Sustituir por", self._nuevo)
        form.addRow("Fuente", self._fuente)
        form.addRow(aviso)
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        form.addRow(botones)

    def texto_nuevo(self) -> str:
        return self._nuevo.text().strip()

    def fuente(self) -> FuenteTexto:
        return _FUENTES[self._fuente.currentIndex()][1]
