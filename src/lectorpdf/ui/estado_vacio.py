"""Estado vacío del área central: sin documento abierto.

Muestra la silueta del dragón Ladón atenuada como marca de agua (monocroma,
tintada al color de texto atenuado del tema, NO al rojo de acento), un texto
secundario y las dos vías para empezar: botón "Abrir…" y la mención de arrastrar
y soltar. Opcionalmente, los últimos documentos recientes como lista clicable.

La silueta procede del asset de marca (PNG afinado); no se dibuja aquí.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lectorpdf.recursos import base_recursos
from lectorpdf.ui import recientes as util_recientes

_ALTO_SILUETA = 200  # px
_OPACIDAD_MARCA = 34  # alfa (0-255): la marca de agua debe susurrar, no gritar


def _ruta_silueta() -> Path:
    return base_recursos() / "assets" / "brand" / "dragon-silhouette.png"


def _tintar(pixmap: QPixmap, color: QColor) -> QPixmap:
    """Tiñe la silueta con `color` usando su canal alfa como máscara."""
    resultado = QPixmap(pixmap.size())
    resultado.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(resultado)
    pintor.drawPixmap(0, 0, pixmap)
    pintor.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    pintor.fillRect(resultado.rect(), color)
    pintor.end()
    return resultado


class EstadoVacio(QWidget):
    """Pantalla de bienvenida cuando no hay ningún documento abierto."""

    abrir_solicitado = Signal()
    reciente_elegido = Signal(str)  # ruta como cadena

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap_base = QPixmap(str(_ruta_silueta()))

        self._silueta = QLabel()
        self._silueta.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._titulo = QLabel("Abre un documento para empezar")
        self._titulo.setObjectName("tituloVacio")
        self._titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._boton = QPushButton("Abrir…")
        self._boton.clicked.connect(self.abrir_solicitado)

        self._pista = QLabel("o arrastra y suelta un PDF en la ventana")
        self._pista.setObjectName("pistaVacio")
        self._pista.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._recientes: list[QPushButton] = []
        self._caja_recientes = QVBoxLayout()
        self._caja_recientes.setSpacing(2)
        self._caja_recientes.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        disposicion = QVBoxLayout(self)
        disposicion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disposicion.setSpacing(14)
        disposicion.addWidget(self._silueta)
        disposicion.addWidget(self._titulo)
        disposicion.addWidget(self._boton, 0, Qt.AlignmentFlag.AlignHCenter)
        disposicion.addWidget(self._pista)
        disposicion.addSpacing(6)
        disposicion.addLayout(self._caja_recientes)

    def recolorear(self, color_marca: str) -> None:
        """Tiñe la silueta al color dado (texto atenuado del tema) y la atenúa."""
        if self._pixmap_base.isNull():
            return
        color = QColor(color_marca)
        color.setAlpha(_OPACIDAD_MARCA)
        escalada = self._pixmap_base.scaledToHeight(
            _ALTO_SILUETA, Qt.TransformationMode.SmoothTransformation
        )
        self._silueta.setPixmap(_tintar(escalada, color))

    def set_recientes(self, rutas: list[str]) -> None:
        """Puebla hasta cuatro recientes clicables; oculta la caja si no hay."""
        while self._caja_recientes.count():
            item = self._caja_recientes.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._recientes = []
        for ruta in rutas[:4]:
            boton = QPushButton(util_recientes.elidir(ruta, 44))
            boton.setObjectName("recienteVacio")
            boton.setFlat(True)
            boton.setToolTip(ruta)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(lambda _=False, r=ruta: self.reciente_elegido.emit(r))
            self._recientes.append(boton)
            self._caja_recientes.addWidget(boton, 0, Qt.AlignmentFlag.AlignHCenter)
