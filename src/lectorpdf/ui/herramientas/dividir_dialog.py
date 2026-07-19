"""Diálogo para dividir un PDF (una por página o por rangos)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from lectorpdf.core.domain.herramientas import Rango
from lectorpdf.ui.herramientas.rangos import parsear_rangos


class DividirDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Dividir PDF")

        self._por_pagina = QRadioButton("Una página por fichero")
        self._por_rangos = QRadioButton("Por rangos:")
        self._por_pagina.setChecked(True)
        self._rangos = QLineEdit()
        self._rangos.setPlaceholderText("p. ej. 1-3, 4-8, 10")

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("¿Cómo dividir el documento?"))
        layout.addWidget(self._por_pagina)
        layout.addWidget(self._por_rangos)
        layout.addWidget(self._rangos)
        layout.addWidget(botones)

    def es_por_pagina(self) -> bool:
        return self._por_pagina.isChecked()

    def rangos(self) -> list[Rango]:
        """Rangos parseados (solo válido si no es 'por página'). Puede lanzar
        ValueError si el texto está mal formado."""
        return parsear_rangos(self._rangos.text())
