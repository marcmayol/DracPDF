"""Control de zoom de la toolbar: zoom− [92 %] zoom+.

Según la maqueta Ladón: lupas alejar/acercar flanqueando un porcentaje editable.
Escribir un porcentaje y confirmar fija el zoom.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QToolButton, QWidget

from lectorpdf.ui.theme.iconos import icono

_MIN_PCT = 10
_MAX_PCT = 800


class ControlZoom(QWidget):
    #: Zoom pedido al escribir el porcentaje (factor: 1.0 = 100 %).
    zoom_pedido = Signal(float)
    acercar = Signal()
    alejar = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._alejar = QToolButton()
        self._alejar.setToolTip("Alejar")
        self._alejar.clicked.connect(self.alejar)
        self._acercar = QToolButton()
        self._acercar.setToolTip("Acercar")
        self._acercar.clicked.connect(self.acercar)

        self._campo = QLineEdit("100")
        self._campo.setObjectName("campoZoom")
        self._campo.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._campo.setFixedWidth(44)  # cabe "800" (zoom máx.) sin recortar
        self._campo.setValidator(QIntValidator(_MIN_PCT, _MAX_PCT, self))
        self._campo.editingFinished.connect(self._al_editar)
        porcentaje = QLabel("%")

        disposicion = QHBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(3)
        disposicion.addWidget(self._alejar)
        disposicion.addWidget(self._campo)
        disposicion.addWidget(porcentaje)
        disposicion.addWidget(self._acercar)

    def recolorear(self, color_hex: str) -> None:
        self._alejar.setIcon(icono("zoom-out", color_hex))
        self._acercar.setIcon(icono("zoom-in", color_hex))

    def set_zoom(self, factor: float) -> None:
        """Refleja la escala actual como porcentaje (1.0 -> "100")."""
        if not self._campo.hasFocus():
            self._campo.setText(str(round(factor * 100)))

    def _al_editar(self) -> None:
        texto = self._campo.text().strip()
        if texto:
            porcentaje = max(_MIN_PCT, min(int(texto), _MAX_PCT))
            self.zoom_pedido.emit(porcentaje / 100.0)
