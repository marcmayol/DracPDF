"""Widget de visor de páginas basado en QGraphicsView.

La escena se compone de un rectángulo de fondo por página (barato, vectorial),
dimensionado a partir de los metadatos del documento. Sobre cada fondo se coloca,
solo cuando la página está visible (± 1), un QGraphicsPixmapItem con la página
renderizada. Los renders se guardan en una caché LRU para no repetirlos al
volver a desplazarse.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPen, QPixmap, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.viewer.cache_lru import CacheLRU
from lectorpdf.ui.viewer.imagen import qpixmap_desde

MARGEN_PX = 12.0
_CAPACIDAD_CACHE = 24
_COLOR_FONDO_VISTA = QColor(82, 86, 89)
_COLOR_PAGINA = QColor(255, 255, 255)
_COLOR_BORDE = QColor(0, 0, 0, 40)

ESCALA_MIN = 0.1
ESCALA_MAX = 8.0
FACTOR_ZOOM = 1.25

_ClaveRender = tuple[int, float]


class ViewerWidget(QGraphicsView):
    """Muestra las páginas de un documento apiladas verticalmente."""

    #: Se emite con el índice (0-based) cuando cambia la página en foco.
    pagina_cambiada = Signal(int)

    def __init__(self, caso_render: RenderizarPagina) -> None:
        super().__init__()
        self._caso_render = caso_render
        self._documento: Documento | None = None
        self._escala: float = 1.0
        self._geometria: dict[int, QRectF] = {}
        self._fondos: dict[int, QGraphicsRectItem] = {}
        self._pixmaps: dict[int, QGraphicsPixmapItem] = {}
        self._cache: CacheLRU[_ClaveRender, QPixmap] = CacheLRU(_CAPACIDAD_CACHE)
        self._pagina_emitida = -1

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setBackgroundBrush(QBrush(_COLOR_FONDO_VISTA))
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

    @property
    def documento(self) -> Documento | None:
        return self._documento

    @property
    def escala(self) -> float:
        return self._escala

    def indices_mostrados(self) -> set[int]:
        """Páginas actualmente pintadas en la escena (para tests/diagnóstico)."""
        return set(self._pixmaps)

    def set_documento(self, documento: Documento, escala: float = 1.0) -> None:
        self._documento = documento
        self._escala = _acotar_escala(escala)
        self._pagina_emitida = -1
        self._cache.limpiar()
        self._construir_escena()
        self._actualizar_paginas_visibles()

    # -- Construcción de la escena ------------------------------------------

    def _construir_escena(self) -> None:
        self._scene.clear()
        self._geometria.clear()
        self._fondos.clear()
        self._pixmaps.clear()
        if self._documento is None:
            self._scene.setSceneRect(QRectF())
            return

        ancho_max = (
            max((p.ancho_pt for p in self._documento.paginas), default=0.0)
            * self._escala
        )

        y = MARGEN_PX
        for pagina in self._documento.paginas:
            ancho_px = pagina.ancho_pt * self._escala
            alto_px = pagina.alto_pt * self._escala
            x = (ancho_max - ancho_px) / 2.0
            rect = QRectF(x, y, ancho_px, alto_px)
            self._geometria[pagina.indice] = rect

            self._fondos[pagina.indice] = self._scene.addRect(
                rect, QPen(_COLOR_BORDE), QBrush(_COLOR_PAGINA)
            )
            y += alto_px + MARGEN_PX

        self._scene.setSceneRect(0, 0, ancho_max + 2 * MARGEN_PX, y)

    # -- Render perezoso ----------------------------------------------------

    def _rect_visible(self) -> QRectF:
        return self.mapToScene(self.viewport().rect()).boundingRect()

    def _indices_en_rect(self, rect_visible: QRectF) -> set[int]:
        """Páginas que intersectan el rectángulo visible, expandidas en ± 1."""
        if not self._geometria:
            return set()
        visibles = [
            i for i, r in self._geometria.items() if r.intersects(rect_visible)
        ]
        if not visibles:
            # Ninguna intersecta (hueco entre páginas): la más cercana en vertical.
            centro_y = rect_visible.center().y()
            visibles = [
                min(
                    self._geometria,
                    key=lambda k: abs(self._geometria[k].center().y() - centro_y),
                )
            ]
        lo = min(visibles) - 1
        hi = max(visibles) + 1
        ultimo = max(self._geometria)
        return {i for i in range(lo, hi + 1) if 0 <= i <= ultimo}

    def _actualizar_paginas_visibles(self) -> None:
        if self._documento is None:
            return
        deseados = self._indices_en_rect(self._rect_visible())

        for indice in list(self._pixmaps):
            if indice not in deseados:
                self._scene.removeItem(self._pixmaps.pop(indice))

        for indice in sorted(deseados):
            self._mostrar_pagina(indice)

        self._emitir_pagina_actual()

    def _mostrar_pagina(self, indice: int) -> None:
        if self._documento is None or indice in self._pixmaps:
            return
        clave: _ClaveRender = (indice, self._escala)
        pixmap = self._cache.obtener(clave)
        if pixmap is None:
            imagen = self._caso_render.ejecutar(self._documento, indice, self._escala)
            pixmap = qpixmap_desde(imagen)
            self._cache.poner(clave, pixmap)

        item = self._scene.addPixmap(pixmap)
        item.setPos(self._geometria[indice].topLeft())
        item.setZValue(1.0)
        self._pixmaps[indice] = item

    # -- Navegación ---------------------------------------------------------

    def pagina_actual(self) -> int:
        """Índice de la página cuyo centro está más cerca del centro de la vista."""
        if not self._geometria:
            return 0
        centro_y = self._rect_visible().center().y()
        return min(
            self._geometria,
            key=lambda k: abs(self._geometria[k].center().y() - centro_y),
        )

    def ir_a_pagina(self, indice: int) -> None:
        if not self._geometria:
            return
        indice = max(0, min(indice, max(self._geometria)))
        self.centerOn(self._geometria[indice].center())
        self._actualizar_paginas_visibles()

    def pagina_siguiente(self) -> None:
        self.ir_a_pagina(self.pagina_actual() + 1)

    def pagina_anterior(self) -> None:
        self.ir_a_pagina(self.pagina_actual() - 1)

    def _emitir_pagina_actual(self) -> None:
        actual = self.pagina_actual()
        if actual != self._pagina_emitida:
            self._pagina_emitida = actual
            self.pagina_cambiada.emit(actual)

    # -- Zoom ---------------------------------------------------------------

    def set_escala(self, escala: float) -> None:
        escala = _acotar_escala(escala)
        if self._documento is None or escala == self._escala:
            self._escala = escala
            return
        actual = self.pagina_actual()
        self._escala = escala
        self._cache.limpiar()
        self._construir_escena()
        self.ir_a_pagina(actual)

    def zoom_acercar(self) -> None:
        self.set_escala(self._escala * FACTOR_ZOOM)

    def zoom_alejar(self) -> None:
        self.set_escala(self._escala / FACTOR_ZOOM)

    def escala_para_ancho(self) -> float:
        """Escala que hace caber el ancho de la página más ancha en la vista."""
        if self._documento is None:
            return self._escala
        ancho_max_pt = max(p.ancho_pt for p in self._documento.paginas)
        disponible = self.viewport().width() - 2 * MARGEN_PX
        return _acotar_escala(disponible / ancho_max_pt)

    def escala_para_pagina(self) -> float:
        """Escala que hace caber la página actual entera (ancho y alto)."""
        if self._documento is None:
            return self._escala
        pagina = self._documento.paginas[self.pagina_actual()]
        escala_ancho = (self.viewport().width() - 2 * MARGEN_PX) / pagina.ancho_pt
        escala_alto = (self.viewport().height() - 2 * MARGEN_PX) / pagina.alto_pt
        return _acotar_escala(min(escala_ancho, escala_alto))

    def ajustar_a_ancho(self) -> None:
        self.set_escala(self.escala_para_ancho())

    def ajustar_a_pagina(self) -> None:
        self.set_escala(self.escala_para_pagina())

    # -- Eventos ------------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_acercar()
            elif delta < 0:
                self.zoom_alejar()
            event.accept()
        else:
            super().wheelEvent(event)

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)
        self._actualizar_paginas_visibles()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._actualizar_paginas_visibles()


def _acotar_escala(escala: float) -> float:
    return max(ESCALA_MIN, min(ESCALA_MAX, escala))
