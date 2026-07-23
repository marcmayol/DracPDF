"""Item de previsualización de imagen sobre la escena, antes de insertarla.

Muestra la imagen dentro de un rectángulo movible y redimensionable. Por defecto
conserva la proporción original (el alto se deriva del ancho); la inserción real
usa `insert_image` con `keep_proportion`.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

from lectorpdf.ui.theme.tokens import OVERLAY_FIRMA

_COLOR_BORDE = QColor(OVERLAY_FIRMA)
_TAM_ASA = 14.0
_ANCHO_MIN = 24.0


class ImagePlacementItem(QGraphicsObject):
    def __init__(
        self, pixmap: QPixmap, ancho: float, conservar_proporcion: bool = True
    ) -> None:
        super().__init__()
        self._pixmap = pixmap
        self._conservar = conservar_proporcion
        self._proporcion = (
            pixmap.height() / pixmap.width() if pixmap.width() else 1.0
        )
        alto = ancho * self._proporcion if conservar_proporcion else ancho
        self._rect = QRectF(0, 0, ancho, max(alto, _ANCHO_MIN))
        self._redimensionando = False
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
        painter.drawPixmap(self._rect.toRect(), self._pixmap)
        painter.setPen(QPen(_COLOR_BORDE, 1.0, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self._rect)
        painter.setPen(QPen(_COLOR_BORDE, 1.0))
        painter.setBrush(QBrush(_COLOR_BORDE))
        painter.drawRect(self._zona_asa())

    # -- Geometría ----------------------------------------------------------

    def redimensionar(self, ancho: float, alto: float) -> None:
        self.prepareGeometryChange()
        ancho = max(_ANCHO_MIN, ancho)
        alto = ancho * self._proporcion if self._conservar else max(_ANCHO_MIN, alto)
        self._rect = QRectF(0, 0, ancho, alto)
        self.update()

    def rect_en_escena(self) -> QRectF:
        return self.mapRectToScene(self._rect)

    def _zona_asa(self) -> QRectF:
        return QRectF(
            self._rect.right() - _TAM_ASA,
            self._rect.bottom() - _TAM_ASA,
            _TAM_ASA,
            _TAM_ASA,
        )

    # -- Interacción --------------------------------------------------------

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._zona_asa().contains(event.pos()):
            self._redimensionando = True
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._redimensionando:
            self.redimensionar(event.pos().x(), event.pos().y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._redimensionando:
            self._redimensionando = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
