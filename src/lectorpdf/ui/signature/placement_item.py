"""Item de previsualización de firma sobre la escena, antes de estampar.

Muestra el PNG de la firma como un rectángulo movible y redimensionable, por
encima de páginas (z=1) y campos (z=2). El redimensionado conserva la proporción
de la firma (no se distorsiona): se arrastra el asa de la esquina inferior
derecha; el resto del rectángulo mueve el item.
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


class SignaturePlacementItem(QGraphicsObject):
    def __init__(self, pixmap: QPixmap, ancho: float, alto: float) -> None:
        super().__init__()
        self._pixmap = pixmap
        self._rect = QRectF(0, 0, ancho, alto)
        self._proporcion = alto / ancho if ancho else 1.0
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
        painter.drawPixmap(self._rect, self._pixmap, QRectF(self._pixmap.rect()))
        painter.setPen(QPen(_COLOR_BORDE, 1.0, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self._rect)
        # Asa de redimensionado (esquina inferior derecha).
        painter.setPen(QPen(_COLOR_BORDE, 1.0))
        painter.setBrush(QBrush(_COLOR_BORDE))
        painter.drawRect(self._zona_asa())

    # -- Geometría ----------------------------------------------------------

    def redimensionar(self, ancho: float, alto: float) -> None:
        self.prepareGeometryChange()
        self._rect = QRectF(0, 0, ancho, alto)
        self.update()

    def redimensionar_desde_ancho(self, nuevo_ancho: float) -> None:
        """Cambia el tamaño conservando la proporción de la firma."""
        ancho = max(_ANCHO_MIN, nuevo_ancho)
        self.redimensionar(ancho, ancho * self._proporcion)

    def tamano(self) -> tuple[float, float]:
        return self._rect.width(), self._rect.height()

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
            super().mousePressEvent(event)  # arrastre = mover

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._redimensionando:
            self.redimensionar_desde_ancho(event.pos().x())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._redimensionando:
            self._redimensionando = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
