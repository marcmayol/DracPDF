"""Item de previsualización de texto sobre la escena, antes de estamparlo.

Muestra el texto dentro de un rectángulo movible y redimensionable (libre, no
proporcional: una caja de texto puede tener cualquier forma). El estampado real
usa la fuente OFL embebida; aquí se aproxima con una familia genérica para situar.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

from lectorpdf.core.domain.anotaciones import Color, FuenteTexto
from lectorpdf.ui.theme.tokens import OVERLAY_FIRMA

_COLOR_BORDE = QColor(OVERLAY_FIRMA)
_TAM_ASA = 14.0
_ANCHO_MIN = 40.0
_ALTO_MIN = 20.0

_ESTILO = {
    FuenteTexto.SERIF: (QFont.StyleHint.Serif, "serif"),
    FuenteTexto.SANS: (QFont.StyleHint.SansSerif, "sans-serif"),
    FuenteTexto.MONO: (QFont.StyleHint.Monospace, "monospace"),
}


class TextPlacementItem(QGraphicsObject):
    def __init__(
        self,
        texto: str,
        fuente: FuenteTexto,
        tamano_px: float,
        color: Color,
        ancho: float,
        alto: float,
    ) -> None:
        super().__init__()
        self._texto = texto
        self._color = QColor.fromRgbF(*color)
        self._rect = QRectF(0, 0, ancho, alto)
        self._redimensionando = False
        hint, familia = _ESTILO[fuente]
        self._font = QFont(familia)
        self._font.setStyleHint(hint)
        self._font.setPointSizeF(max(1.0, tamano_px))
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
        painter.setFont(self._font)
        painter.setPen(QPen(self._color))
        painter.drawText(
            self._rect.adjusted(2, 2, -2, -2),
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            | int(Qt.TextFlag.TextWordWrap),
            self._texto,
        )
        painter.setPen(QPen(_COLOR_BORDE, 1.0, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self._rect)
        painter.setPen(QPen(_COLOR_BORDE, 1.0))
        painter.setBrush(QBrush(_COLOR_BORDE))
        painter.drawRect(self._zona_asa())

    # -- Geometría ----------------------------------------------------------

    def redimensionar(self, ancho: float, alto: float) -> None:
        self.prepareGeometryChange()
        self._rect = QRectF(0, 0, max(_ANCHO_MIN, ancho), max(_ALTO_MIN, alto))
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
