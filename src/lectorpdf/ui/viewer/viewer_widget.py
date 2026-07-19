"""Widget de visor de páginas basado en QGraphicsView.

La escena se compone de un rectángulo de fondo por página (barato, vectorial),
dimensionado a partir de los metadatos del documento. Sobre cada fondo se coloca
un QGraphicsPixmapItem con la página renderizada.

En esta fase el render es voraz (todas las páginas). El render perezoso y la
caché LRU se añaden en la tarea 4.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.viewer.imagen import qpixmap_desde

MARGEN_PX = 12.0
_COLOR_FONDO_VISTA = QColor(82, 86, 89)
_COLOR_PAGINA = QColor(255, 255, 255)
_COLOR_BORDE = QColor(0, 0, 0, 40)


class ViewerWidget(QGraphicsView):
    """Muestra las páginas de un documento apiladas verticalmente."""

    def __init__(self, caso_render: RenderizarPagina) -> None:
        super().__init__()
        self._caso_render = caso_render
        self._documento: Documento | None = None
        self._escala: float = 1.0
        self._geometria: dict[int, QRectF] = {}
        self._fondos: dict[int, QGraphicsRectItem] = {}
        self._pixmaps: dict[int, QGraphicsPixmapItem] = {}

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setBackgroundBrush(QBrush(_COLOR_FONDO_VISTA))
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.setRenderHints(self.renderHints())

    @property
    def documento(self) -> Documento | None:
        return self._documento

    @property
    def escala(self) -> float:
        return self._escala

    def set_documento(self, documento: Documento, escala: float = 1.0) -> None:
        self._documento = documento
        self._escala = escala
        self._construir_escena()
        self._refrescar()

    # -- Construcción de la escena ------------------------------------------

    def _construir_escena(self) -> None:
        self._scene.clear()
        self._geometria.clear()
        self._fondos.clear()
        self._pixmaps.clear()
        if self._documento is None:
            self._scene.setSceneRect(QRectF())
            return

        ancho_max = max(
            (p.ancho_pt for p in self._documento.paginas), default=0.0
        ) * self._escala

        y = MARGEN_PX
        for pagina in self._documento.paginas:
            ancho_px = pagina.ancho_pt * self._escala
            alto_px = pagina.alto_pt * self._escala
            x = (ancho_max - ancho_px) / 2.0
            rect = QRectF(x, y, ancho_px, alto_px)
            self._geometria[pagina.indice] = rect

            fondo = self._scene.addRect(
                rect, QPen(_COLOR_BORDE), QBrush(_COLOR_PAGINA)
            )
            self._fondos[pagina.indice] = fondo

            y += alto_px + MARGEN_PX

        self._scene.setSceneRect(
            0, 0, ancho_max + 2 * MARGEN_PX, y
        )

    def _refrescar(self) -> None:
        """Renderiza y muestra todas las páginas (voraz; ver tarea 4)."""
        for indice in self._geometria:
            self._mostrar_pagina(indice)

    def _mostrar_pagina(self, indice: int) -> None:
        if self._documento is None or indice in self._pixmaps:
            return
        imagen = self._caso_render.ejecutar(self._documento, indice, self._escala)
        pixmap = qpixmap_desde(imagen)
        item = self._scene.addPixmap(pixmap)
        rect = self._geometria[indice]
        item.setPos(rect.topLeft())
        item.setZValue(1.0)
        self._pixmaps[indice] = item
