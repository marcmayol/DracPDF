"""Item de previsualización de firma sobre la escena, antes de estampar.

Muestra el PNG de la firma como un rectángulo movible con borde discontinuo,
por encima de páginas (z=1) y campos (z=2). El redimensionado interactivo se
añade en la tarea 5; aquí ya expone `redimensionar` para colocarlo con tamaño.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QStyleOptionGraphicsItem,
    QWidget,
)

_COLOR_BORDE = QColor(37, 99, 235)


class SignaturePlacementItem(QGraphicsObject):
    def __init__(self, pixmap: QPixmap, ancho: float, alto: float) -> None:
        super().__init__()
        self._pixmap = pixmap
        self._rect = QRectF(0, 0, ancho, alto)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(3.0)

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        painter.drawPixmap(self._rect, self._pixmap, QRectF(self._pixmap.rect()))
        pluma = QPen(_COLOR_BORDE, 1.0, Qt.PenStyle.DashLine)
        painter.setPen(pluma)
        painter.drawRect(self._rect)

    def redimensionar(self, ancho: float, alto: float) -> None:
        self.prepareGeometryChange()
        self._rect = QRectF(0, 0, ancho, alto)
        self.update()

    def tamano(self) -> tuple[float, float]:
        return self._rect.width(), self._rect.height()

    def rect_en_escena(self) -> QRectF:
        return self.mapRectToScene(self._rect)
