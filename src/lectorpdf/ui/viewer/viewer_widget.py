"""Widget de visor de páginas basado en QGraphicsView.

La escena se compone de un rectángulo de fondo por página (barato, vectorial),
dimensionado a partir de los metadatos del documento. Sobre cada fondo se coloca,
solo cuando la página está visible (± 1), un QGraphicsPixmapItem con la página
renderizada. Los renders se guardan en una caché LRU para no repetirlos al
volver a desplazarse.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum, auto

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPen,
    QPixmap,
    QResizeEvent,
    QTransform,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.forms.coordenadas import punto_escena_a_pdf, rect_pdf_a_escena
from lectorpdf.ui.theme.tokens import PAPEL, PAPEL_BORDE, TEMA_POR_DEFECTO
from lectorpdf.ui.viewer.cache_lru import CacheLRU
from lectorpdf.ui.viewer.imagen import qpixmap_desde

MARGEN_PX = 12.0
_CAPACIDAD_CACHE = 24
_COLOR_PAGINA = QColor(PAPEL)
_COLOR_BORDE = QColor(PAPEL_BORDE)

ESCALA_MIN = 0.1
ESCALA_MAX = 8.0
FACTOR_ZOOM = 1.25

_ClaveRender = tuple[int, float]


class ModoAjuste(Enum):
    """Modo de ajuste persistente del zoom (se re-aplica al cambiar el tamaño)."""

    LIBRE = auto()  # zoom manual
    ANCHO = auto()  # ajustar al ancho
    PAGINA = auto()  # ajustar la página entera


class ViewerWidget(QGraphicsView):
    """Muestra las páginas de un documento apiladas verticalmente."""

    #: Se emite con el índice (0-based) cuando cambia la página en foco.
    pagina_cambiada = Signal(int)
    #: Se emite tras reconstruir la escena (que se vació): las capas superpuestas
    #: deben descartar sus items previos, ya destruidos por el clear.
    escena_reconstruida = Signal()
    #: Se emite tras cada refresco de páginas visibles (scroll/zoom/apertura).
    vista_actualizada = Signal()
    #: Se emite con el nombre del modo de ajuste al cambiar (para persistirlo).
    modo_ajuste_cambiado = Signal(str)
    #: Se emite con la escala (1.0 = 100 %) al cambiar el zoom.
    escala_cambiada = Signal(float)

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
        self._modo = ModoAjuste.LIBRE
        self._doble = False
        self._rotacion = 0  # grados de rotación de vista: 0, 90, 180, 270

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setBackgroundBrush(QBrush(QColor(TEMA_POR_DEFECTO.canvas)))
        self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

    def aplicar_fondo(self, color_hex: str) -> None:
        """Fija el color del lienzo tras las páginas (token `canvas` del tema)."""
        self.setBackgroundBrush(QBrush(QColor(color_hex)))

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
        self._rotacion = 0  # la rotación de vista no se hereda entre documentos
        self._cache.limpiar()
        self._construir_escena()
        self._actualizar_paginas_visibles()
        self._refit_si_procede()  # respeta el modo de ajuste persistente

    # -- Construcción de la escena ------------------------------------------

    def _dims_pt(self, pagina: Pagina) -> tuple[float, float]:
        """Dimensiones (ancho, alto) en puntos aplicando la rotación de vista."""
        if self._rotacion in (90, 270):
            return pagina.alto_pt, pagina.ancho_pt
        return pagina.ancho_pt, pagina.alto_pt

    def _filas(self) -> list[Sequence[Pagina]]:
        """Páginas agrupadas en filas: una por fila, o dos si es doble página."""
        if self._documento is None:
            return []
        paginas = self._documento.paginas
        if self._doble:
            return [paginas[i : i + 2] for i in range(0, len(paginas), 2)]
        return [[p] for p in paginas]

    def _ancho_fila_px(self, fila: Sequence[Pagina]) -> float:
        paginas = sum(self._dims_pt(p)[0] for p in fila) * self._escala
        return paginas + MARGEN_PX * (len(fila) - 1)  # separación entre las dos

    def _construir_escena(self) -> None:
        self._scene.clear()
        self._geometria.clear()
        self._fondos.clear()
        self._pixmaps.clear()
        if self._documento is None:
            self._scene.setSceneRect(QRectF())
            return

        filas = self._filas()
        ancho_max = max((self._ancho_fila_px(f) for f in filas), default=0.0)

        y = MARGEN_PX
        for fila in filas:
            alto_fila = max(self._dims_pt(p)[1] for p in fila) * self._escala
            x = (ancho_max - self._ancho_fila_px(fila)) / 2.0
            for pagina in fila:
                aw, ah = self._dims_pt(pagina)
                ancho_px = aw * self._escala
                alto_px = ah * self._escala
                yy = y + (alto_fila - alto_px) / 2.0  # centrado vertical en la fila
                rect = QRectF(x, yy, ancho_px, alto_px)
                self._geometria[pagina.indice] = rect
                self._fondos[pagina.indice] = self._scene.addRect(
                    rect, QPen(_COLOR_BORDE), QBrush(_COLOR_PAGINA)
                )
                x += ancho_px + MARGEN_PX
            y += alto_fila + MARGEN_PX

        self._scene.setSceneRect(0, 0, ancho_max + 2 * MARGEN_PX, y)
        self.escena_reconstruida.emit()

    def rect_pagina(self, indice: int) -> QRectF | None:
        """Rectángulo de la página en coordenadas de escena (o None si no existe)."""
        return self._geometria.get(indice)

    def pagina_en_punto(self, punto: QPointF) -> int | None:
        """Índice de la página cuyo rectángulo contiene el punto de escena."""
        for indice, rect in self._geometria.items():
            if rect.contains(punto):
                return indice
        return None

    def pagina_y_punto_pt(self, pos: QPoint) -> tuple[int, float, float] | None:
        """De un punto del viewport a (página, x, y) en puntos PDF, o None si el
        punto no cae sobre ninguna página. Lo usan las capas de selección y
        enlaces para traducir el ratón a coordenadas del documento."""
        escena = self.mapToScene(pos)
        pagina = self.pagina_en_punto(escena)
        if pagina is None:
            return None
        rect = self._geometria[pagina]
        x, y = punto_escena_a_pdf(
            escena.x(), escena.y(), rect.left(), rect.top(), self._escala
        )
        return pagina, x, y

    def invalidar_pagina(self, indice: int) -> None:
        """Purga el render cacheado de una página (todas las escalas) y la
        vuelve a renderizar. Se usa tras estampar una firma en ella."""
        for clave in list(self._cache.claves()):
            if clave[0] == indice:
                self._cache.descartar(clave)
        item = self._pixmaps.pop(indice, None)
        if item is not None:
            self._scene.removeItem(item)
        self._actualizar_paginas_visibles()

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
        self.vista_actualizada.emit()

    def _mostrar_pagina(self, indice: int) -> None:
        if self._documento is None or indice in self._pixmaps:
            return
        clave: _ClaveRender = (indice, self._escala)
        pixmap = self._cache.obtener(clave)
        if pixmap is None:
            imagen = self._caso_render.ejecutar(self._documento, indice, self._escala)
            pixmap = qpixmap_desde(imagen)
            self._cache.poner(clave, pixmap)

        if self._rotacion:
            pixmap = pixmap.transformed(QTransform().rotate(self._rotacion))
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

    def centrar_en(self, pagina: int, rect_pt: RectanguloPt) -> None:
        """Centra la vista sobre un rect (en puntos PDF) de una página, con la
        misma traducción página→escena que los formularios. Lo usan la búsqueda
        (llevar la coincidencia activa a la vista) y los enlaces internos."""
        rect_pagina = self._geometria.get(pagina)
        if rect_pagina is None:
            return
        r = rect_pdf_a_escena(
            rect_pt, rect_pagina.left(), rect_pagina.top(), self._escala
        )
        self.centerOn(r.x + r.ancho / 2.0, r.y + r.alto / 2.0)
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
        """Zoom manual: cancela el modo de ajuste persistente."""
        self._set_modo(ModoAjuste.LIBRE)
        self._aplicar_escala(escala)

    def _set_modo(self, modo: ModoAjuste) -> None:
        if modo != self._modo:
            self._modo = modo
            self.modo_ajuste_cambiado.emit(modo.name)

    def modo_ajuste(self) -> str:
        return self._modo.name

    def set_modo_ajuste(self, nombre: str) -> None:
        """Restaura el modo de ajuste por su nombre (persistencia). Lo aplica si
        ya hay documento; si no, quedará listo para el siguiente que se abra."""
        try:
            modo = ModoAjuste[nombre]
        except KeyError:
            return
        self._modo = modo
        self._refit_si_procede()

    def _aplicar_escala(self, escala: float) -> None:
        escala = _acotar_escala(escala)
        if self._documento is None or escala == self._escala:
            self._escala = escala
        else:
            actual = self.pagina_actual()
            self._escala = escala
            self._cache.limpiar()
            self._construir_escena()
            self.ir_a_pagina(actual)
        self.escala_cambiada.emit(self._escala)

    def zoom_acercar(self) -> None:
        self.set_escala(self._escala * FACTOR_ZOOM)

    def zoom_alejar(self) -> None:
        self.set_escala(self._escala / FACTOR_ZOOM)

    def _refit_si_procede(self) -> None:
        """Re-aplica el ajuste si hay un modo persistente activo (ancho/página)."""
        if self._modo == ModoAjuste.ANCHO:
            self._aplicar_escala(self.escala_para_ancho())
        elif self._modo == ModoAjuste.PAGINA:
            self._aplicar_escala(self.escala_para_pagina())

    def escala_para_ancho(self) -> float:
        """Escala que hace caber el ancho del contenido más ancho (una página, o
        el par de páginas en modo doble) en la vista."""
        if self._documento is None:
            return self._escala
        ancho_max_pt = max(
            sum(self._dims_pt(p)[0] for p in fila) for fila in self._filas()
        )
        disponible = self.viewport().width() - 2 * MARGEN_PX
        return _acotar_escala(disponible / ancho_max_pt)

    def escala_para_pagina(self) -> float:
        """Escala que hace caber la página actual entera (ancho y alto). En modo
        doble el ancho disponible se reparte entre las dos páginas."""
        if self._documento is None:
            return self._escala
        aw, ah = self._dims_pt(self._documento.paginas[self.pagina_actual()])
        factor = 2 if self._doble else 1
        escala_ancho = (self.viewport().width() - 2 * MARGEN_PX) / (aw * factor)
        escala_alto = (self.viewport().height() - 2 * MARGEN_PX) / ah
        return _acotar_escala(min(escala_ancho, escala_alto))

    def ajustar_a_ancho(self) -> None:
        self._set_modo(ModoAjuste.ANCHO)
        self._aplicar_escala(self.escala_para_ancho())

    def ajustar_a_pagina(self) -> None:
        self._set_modo(ModoAjuste.PAGINA)
        self._aplicar_escala(self.escala_para_pagina())

    # -- Doble página y rotación de vista (solo presentación) ---------------

    def set_doble_pagina(self, doble: bool) -> None:
        if doble == self._doble:
            return
        self._doble = doble
        self._reconstruir_conservando_pagina()

    def doble_pagina(self) -> bool:
        return self._doble

    def rotar_vista(self, grados: int = 90) -> None:
        """Rota la presentación (no el documento) en múltiplos de 90 grados. El
        pixmap se rota al mostrarlo, así que la caché de render sigue siendo
        válida (guarda la página sin rotar)."""
        self._rotacion = (self._rotacion + grados) % 360
        self._reconstruir_conservando_pagina()

    def rotacion(self) -> int:
        return self._rotacion

    def _reconstruir_conservando_pagina(self) -> None:
        actual = self.pagina_actual()
        self._construir_escena()
        self.ir_a_pagina(actual)
        self._refit_si_procede()

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
        self._refit_si_procede()  # el ajuste ancho/página se re-aplica al tamaño
        self._actualizar_paginas_visibles()


def _acotar_escala(escala: float) -> float:
    return max(ESCALA_MIN, min(ESCALA_MAX, escala))
