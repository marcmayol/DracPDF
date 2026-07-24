"""Banda no modal que anuncia una versión nueva (Fase 10, tarea 5).

Muestra "DracPDF X.Y.Z disponible" con sus notas y un botón Actualizar. Se
estiliza con la propiedad dinámica `infoBanner` del QSS, como la banda de firmado.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from lectorpdf.core.domain.actualizacion import Manifiesto


class BandaActualizacion(QFrame):
    #: El usuario pulsa Actualizar (con el manifiesto anunciado).
    actualizar_solicitado = Signal(object)  # Manifiesto
    #: El usuario descarta la banda.
    descartada = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("infoBanner", "true")
        self._manifiesto: Manifiesto | None = None

        self._etiqueta = QLabel()
        self._etiqueta.setWordWrap(True)
        self._boton = QPushButton("Actualizar")
        self._boton.clicked.connect(self._al_actualizar)
        self._cerrar = QPushButton("✕")
        self._cerrar.setFlat(True)
        self._cerrar.setFixedWidth(28)
        self._cerrar.clicked.connect(self._al_descartar)

        disposicion = QHBoxLayout(self)
        disposicion.setContentsMargins(12, 4, 8, 4)
        disposicion.addWidget(self._etiqueta, 1)
        disposicion.addWidget(self._boton)
        disposicion.addWidget(self._cerrar)
        self.hide()

    def mostrar_para(self, manifiesto: Manifiesto) -> None:
        self._manifiesto = manifiesto
        texto = f"<b>DracPDF {manifiesto.version} disponible.</b>"
        if manifiesto.notas:
            texto += f" {manifiesto.notas}"
        self._etiqueta.setText(texto)
        self.show()

    def _al_actualizar(self) -> None:
        if self._manifiesto is not None:
            self.actualizar_solicitado.emit(self._manifiesto)

    def _al_descartar(self) -> None:
        self.hide()
        self.descartada.emit()
