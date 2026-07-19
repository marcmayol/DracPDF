"""Carga de los iconos SVG monocromos del diseño, recoloreados por tema.

Los SVG usan `stroke="currentColor"`; se sustituye por el color del token del
tema y se rasterizan con QSvgRenderer. El diseño pide renderizar a 20 px dentro
de un botón de 30×30.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from lectorpdf.recursos import base_recursos

_DIR_ICONOS = base_recursos() / "assets" / "icons"
_TAM_POR_DEFECTO = 20


def icono(nombre: str, color: str, tamano: int = _TAM_POR_DEFECTO) -> QIcon:
    """Devuelve el icono `nombre` recoloreado a `color` (#RRGGBB)."""
    ruta = _DIR_ICONOS / f"{nombre}.svg"
    svg = ruta.read_text(encoding="utf-8").replace("currentColor", color)
    renderizador = QSvgRenderer(QByteArray(svg.encode("utf-8")))

    pixmap = QPixmap(tamano, tamano)
    pixmap.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(pixmap)
    renderizador.render(pintor)
    pintor.end()
    return QIcon(pixmap)
