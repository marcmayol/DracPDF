"""Diálogo de Word → PDF: tamaño de página, márgenes y etiquetado honesto.

Deja claro que la conversión conserva el contenido y la estructura, no el diseño
exacto del original (es un "reformateado").
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QWidget,
)

from lectorpdf.core.domain.conversion import A4, CARTA, ConfigPagina

_TAMANOS: dict[str, ConfigPagina] = {"A4": A4, "Carta": CARTA}
_AVISO = (
    "Conserva el contenido y la estructura (texto seleccionable, tablas, listas, "
    "negritas e imágenes), no el diseño exacto del documento original."
)


class ConversionWordDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Convertir Word a PDF (reformateado)")

        aviso = QLabel(_AVISO)
        aviso.setWordWrap(True)

        self._tamano = QComboBox()
        self._tamano.addItems(list(_TAMANOS))
        self._margen = QSpinBox()
        self._margen.setRange(0, 50)
        self._margen.setValue(20)
        self._margen.setSuffix(" mm")

        form = QFormLayout(self)
        form.addRow(aviso)
        form.addRow("Tamaño de página:", self._tamano)
        form.addRow("Margen:", self._margen)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        form.addRow(botones)

    def config(self) -> ConfigPagina:
        base = _TAMANOS[self._tamano.currentText()]
        return ConfigPagina(
            ancho_mm=base.ancho_mm,
            alto_mm=base.alto_mm,
            margen_mm=float(self._margen.value()),
        )
