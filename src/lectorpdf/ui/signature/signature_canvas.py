"""Lienzo de dibujo de firma.

Captura trazos con ratón o stylus (varios trazos con pen up/down), los suaviza
con curvas (ver `suavizado`) y los pinta sobre un fondo transparente.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QBuffer, QByteArray, QIODeviceBase, QPointF, Qt
from PySide6.QtGui import (
    QColor,
    QImage,
    QImageWriter,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QTabletEvent,
)
from PySide6.QtWidgets import QWidget

from lectorpdf.ui.signature.suavizado import Punto, curva_catmull_rom
from lectorpdf.ui.theme.tokens import TINTA_FIRMA

_ANCHO_TRAZO = 2.8
_COLOR_TRAZO = QColor(TINTA_FIRMA)
_MARGEN_EXPORT = 8


class SignatureCanvas(QWidget):
    """Widget de captura de firma sobre fondo transparente."""

    def __init__(self) -> None:
        super().__init__()
        self._trazos: list[list[QPointF]] = []
        self.setAttribute(Qt.WidgetAttribute.WA_StaticContents)
        self.setMinimumSize(400, 160)

    # -- API pública --------------------------------------------------------

    def limpiar(self) -> None:
        self._trazos = []
        self.update()

    def esta_vacio(self) -> bool:
        return not any(self._trazos)

    def trazos(self) -> list[list[Punto]]:
        """Copia de los trazos como puntos (para tests/diagnóstico)."""
        return [[(p.x(), p.y()) for p in trazo] for trazo in self._trazos]

    def exportar_png(self, margen: int = _MARGEN_EXPORT) -> bytes:
        """Renderiza los trazos a un PNG recortado, con fondo transparente."""
        if self.esta_vacio():
            raise ValueError("El lienzo está vacío: no hay firma que exportar")
        x0, y0, x1, y1 = self._caja_trazos()
        borde = margen + _ANCHO_TRAZO
        ancho = math.ceil(x1 - x0 + 2 * borde)
        alto = math.ceil(y1 - y0 + 2 * borde)

        imagen = QImage(ancho, alto, QImage.Format.Format_ARGB32)
        imagen.fill(Qt.GlobalColor.transparent)
        pintor = QPainter(imagen)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.translate(borde - x0, borde - y0)
        self._pintar_trazos(pintor)
        pintor.end()

        datos = QByteArray()
        buffer = QBuffer(datos)
        buffer.open(QIODeviceBase.OpenModeFlag.WriteOnly)
        escritor = QImageWriter(buffer, QByteArray(b"PNG"))
        escritor.write(imagen)
        return bytes(datos.data())

    def _caja_trazos(self) -> tuple[float, float, float, float]:
        puntos = [p for trazo in self._trazos for p in trazo]
        xs = [p.x() for p in puntos]
        ys = [p.y() for p in puntos]
        return min(xs), min(ys), max(xs), max(ys)

    # -- Captura ------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._iniciar_trazo(event.position())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._continuar_trazo(event.position())

    def tabletEvent(self, event: QTabletEvent) -> None:
        tipo = event.type()
        if tipo == QTabletEvent.Type.TabletPress:
            self._iniciar_trazo(event.position())
        elif tipo == QTabletEvent.Type.TabletMove:
            self._continuar_trazo(event.position())
        event.accept()

    def _iniciar_trazo(self, punto: QPointF) -> None:
        self._trazos.append([QPointF(punto)])
        self.update()

    def _continuar_trazo(self, punto: QPointF) -> None:
        if not self._trazos:
            self._trazos.append([])
        self._trazos[-1].append(QPointF(punto))
        self.update()

    # -- Pintado ------------------------------------------------------------

    def paintEvent(self, event: object) -> None:
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._pintar_trazos(pintor)
        pintor.end()

    def _pintar_trazos(self, pintor: QPainter) -> None:
        pluma = QPen(_COLOR_TRAZO, _ANCHO_TRAZO)
        pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
        pluma.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pintor.setPen(pluma)
        for trazo in self._trazos:
            if len(trazo) == 1:
                # Un solo punto: un pequeño círculo (punto de la firma).
                pintor.setBrush(_COLOR_TRAZO)
                pintor.drawEllipse(trazo[0], _ANCHO_TRAZO / 2, _ANCHO_TRAZO / 2)
                pintor.setBrush(Qt.BrushStyle.NoBrush)
            elif len(trazo) >= 2:
                pintor.drawPath(_path_de(trazo))


def _path_de(trazo: list[QPointF]) -> QPainterPath:
    puntos: list[Punto] = [(p.x(), p.y()) for p in trazo]
    path = QPainterPath()
    path.moveTo(trazo[0])
    for _, c1, c2, fin in curva_catmull_rom(puntos):
        path.cubicTo(QPointF(*c1), QPointF(*c2), QPointF(*fin))
    return path
