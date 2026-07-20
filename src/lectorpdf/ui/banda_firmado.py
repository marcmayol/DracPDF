"""Banda no modal que avisa de que el documento está firmado (edición bloqueada).

Ofrece como vía de escape guardar una copia editable. Se estiliza con la
propiedad dinámica `infoBanner` del QSS (ámbar del tema).
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


class BandaFirmado(QFrame):
    #: El usuario pide guardar una copia editable del documento firmado.
    copia_solicitada = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("infoBanner", "true")

        etiqueta = QLabel(
            "Documento firmado: la edición está bloqueada para preservar la firma."
        )
        self._boton = QPushButton("Guardar una copia editable")
        self._boton.clicked.connect(self.copia_solicitada)

        disposicion = QHBoxLayout(self)
        disposicion.setContentsMargins(12, 4, 12, 4)
        disposicion.addWidget(etiqueta)
        disposicion.addStretch(1)
        disposicion.addWidget(self._boton)
