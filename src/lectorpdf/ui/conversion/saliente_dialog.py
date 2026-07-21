"""Diálogo de las conversiones salientes: rango de páginas y opciones.

Rango de páginas elegible (vacío = documento completo) y, para HTML, si las
imágenes van embebidas o en una carpeta aneja.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QWidget,
)

from lectorpdf.core.domain.herramientas import Rango
from lectorpdf.ui.herramientas.rangos import parsear_rango


class ConversionSalienteDialog(QDialog):
    def __init__(
        self,
        titulo: str,
        num_paginas: int,
        con_opcion_imagenes: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(titulo)

        self._rango = QLineEdit()
        self._rango.setPlaceholderText(f"Todas (1-{num_paginas}); p. ej. 1-3")

        form = QFormLayout(self)
        form.addRow("Páginas:", self._rango)

        self._imagenes: QCheckBox | None = None
        if con_opcion_imagenes:
            self._imagenes = QCheckBox("Imágenes embebidas (si no, en carpeta aneja)")
            self._imagenes.setChecked(True)
            form.addRow(self._imagenes)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        form.addRow(botones)

    def rango(self) -> Rango | None:
        """Rango elegido, o None para el documento completo. Puede lanzar
        ValueError si el texto está mal formado."""
        return parsear_rango(self._rango.text())

    def imagenes_embebidas(self) -> bool:
        return self._imagenes is None or self._imagenes.isChecked()
