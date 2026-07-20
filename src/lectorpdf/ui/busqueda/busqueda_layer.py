"""Capa de resaltado de coincidencias de búsqueda sobre el visor.

Pinta un rectángulo vectorial por coincidencia (barato, como los fondos de
página), con el mismo mapeo página→escena que los formularios. La coincidencia
activa se pinta con un tinte más opaco y un borde; el resto, con un tinte suave.
Se redibuja al reconstruirse la escena (apertura/zoom), porque el `clear` de la
escena destruye los items previos.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QGraphicsRectItem

from lectorpdf.core.domain.contenido import Coincidencia
from lectorpdf.ui.forms.coordenadas import rect_pdf_a_escena
from lectorpdf.ui.theme import tokens
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_Z_RESALTADO = 1.5  # entre el pixmap de página (z = 1) y los campos (z = 2)
_ANCHO_BORDE_ACTIVA = 1.5


def _color(color_escena: tokens.ColorEscena) -> QColor:
    c = QColor(color_escena.hex)
    c.setAlpha(color_escena.alfa)
    return c


class BusquedaLayer:
    def __init__(self, visor: ViewerWidget) -> None:
        self._visor = visor
        self._coincidencias: tuple[Coincidencia, ...] = ()
        self._activa = -1
        self._items: list[QGraphicsRectItem] = []
        visor.escena_reconstruida.connect(self._redibujar)

    def set_coincidencias(
        self, coincidencias: tuple[Coincidencia, ...], activa: int = -1
    ) -> None:
        self._coincidencias = coincidencias
        self._activa = activa
        self._redibujar()

    def set_activa(self, activa: int) -> None:
        self._activa = activa
        self._redibujar()

    def limpiar(self) -> None:
        self.set_coincidencias((), -1)

    def items(self) -> list[QGraphicsRectItem]:
        """Items pintados (para tests/diagnóstico)."""
        return list(self._items)

    def _redibujar(self) -> None:
        escena = self._visor.scene()
        if escena is None:
            return
        for item in self._items:
            if item.scene() is escena:
                escena.removeItem(item)
        self._items.clear()

        pincel_resto = QBrush(_color(tokens.BUSQUEDA_COINCIDENCIA))
        pincel_activa = QBrush(_color(tokens.BUSQUEDA_ACTIVA))
        pluma_activa = QPen(QColor(tokens.BUSQUEDA_ACTIVA_BORDE), _ANCHO_BORDE_ACTIVA)
        pluma_resto = QPen(Qt.PenStyle.NoPen)

        for indice, coincidencia in enumerate(self._coincidencias):
            rect_pagina = self._visor.rect_pagina(coincidencia.pagina)
            if rect_pagina is None:
                continue
            r = rect_pdf_a_escena(
                coincidencia.rect_pt,
                rect_pagina.left(),
                rect_pagina.top(),
                self._visor.escala,
            )
            es_activa = indice == self._activa
            item = escena.addRect(
                QRectF(r.x, r.y, r.ancho, r.alto),
                pluma_activa if es_activa else pluma_resto,
                pincel_activa if es_activa else pincel_resto,
            )
            item.setZValue(_Z_RESALTADO)
            self._items.append(item)
