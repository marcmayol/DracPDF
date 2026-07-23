"""Capa de selección y copia de texto sobre el visor.

Filtra los eventos de ratón del viewport para arrastrar una selección sobre las
palabras de la página (mismo mapeo página→escena que los formularios), con doble
clic = palabra y triple clic = párrafo, y Ctrl+C para copiar. La lógica de qué
palabras entran en la selección es pura y vive en `seleccion.py`; aquí solo se
traduce ratón→coordenadas, se pinta el resaltado y se copia al portapapeles.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QGuiApplication,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QPen,
)
from PySide6.QtWidgets import QGraphicsRectItem

from lectorpdf.core.domain.contenido import PalabraTexto
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.obtener_palabras import ObtenerPalabras
from lectorpdf.ui.forms.coordenadas import rect_pdf_a_escena
from lectorpdf.ui.seleccion import seleccion
from lectorpdf.ui.theme import tokens
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_Z_SELECCION = 1.4  # bajo el resaltado de búsqueda (1.5) y los campos (2)
_TOLERANCIA_TRIPLE_PX = 4.0


def _pincel_seleccion() -> QBrush:
    c = QColor(tokens.SELECCION_TEXTO.hex)
    c.setAlpha(tokens.SELECCION_TEXTO.alfa)
    return QBrush(c)


class SeleccionLayer(QObject):
    def __init__(self, visor: ViewerWidget, caso_palabras: ObtenerPalabras) -> None:
        super().__init__()
        self._visor = visor
        self._caso = caso_palabras
        self._documento: Documento | None = None
        self._cache: dict[int, tuple[PalabraTexto, ...]] = {}
        self._items: list[QGraphicsRectItem] = []

        # Selección activa: página, palabras de esa página y rango [inicio, fin].
        self._sel_pagina = -1
        self._sel_palabras: tuple[PalabraTexto, ...] = ()
        self._sel_inicio = -1
        self._sel_fin = -1

        # Arrastre y detección de racha de clics (doble/triple).
        self._arrastrando = False
        self._anclaje = -1
        self._racha = 0
        self._ultimo_click_ms = 0
        self._ultimo_pos = (0.0, 0.0)

        visor.viewport().installEventFilter(self)
        visor.installEventFilter(self)
        visor.escena_reconstruida.connect(self._repintar)

    def set_documento(self, documento: Documento | None) -> None:
        self._documento = documento
        self._cache.clear()
        self.limpiar()

    def seleccionar_todo(self, pagina: int) -> None:
        """Selecciona todo el texto de una página (acción Edición → Seleccionar
        todo). Composición sobre las palabras ya disponibles; sin lógica nueva."""
        palabras = self._palabras(pagina)
        if palabras:
            self._fijar_seleccion(pagina, palabras, 0, len(palabras) - 1)

    # -- Estado de la selección (API/tests) ---------------------------------

    def texto_seleccionado(self) -> str:
        if self._sel_inicio < 0 or self._sel_fin < 0:
            return ""
        return seleccion.texto_de(self._sel_palabras, self._sel_inicio, self._sel_fin)

    def seleccion_actual(self) -> tuple[int, tuple[RectanguloPt, ...]] | None:
        """Página (0-based) y rects en puntos PDF de las palabras seleccionadas,
        o None si no hay selección (para marcar/corregir)."""
        if self._sel_inicio < 0 or self._sel_fin < 0:
            return None
        lo, hi = sorted((self._sel_inicio, self._sel_fin))
        rects = tuple(p.rect_pt for p in self._sel_palabras[lo : hi + 1])
        if not rects:
            return None
        return self._sel_pagina, rects

    def copiar(self) -> str:
        """Copia el texto seleccionado al portapapeles y lo devuelve."""
        texto = self.texto_seleccionado()
        if texto:
            portapapeles = QGuiApplication.clipboard()
            if portapapeles is not None:
                portapapeles.setText(texto)
        return texto

    def limpiar(self) -> None:
        self._sel_pagina = -1
        self._sel_palabras = ()
        self._sel_inicio = -1
        self._sel_fin = -1
        self._repintar()

    def items(self) -> list[QGraphicsRectItem]:
        return list(self._items)

    # -- Palabras por página (con caché) ------------------------------------

    def _palabras(self, pagina: int) -> tuple[PalabraTexto, ...]:
        if self._documento is None:
            return ()
        if pagina not in self._cache:
            self._cache[pagina] = self._caso.ejecutar(self._documento, pagina)
        return self._cache[pagina]

    # -- Traducción ratón → (página, punto en puntos) -----------------------

    def _pagina_y_punto(self, pos: QPoint) -> tuple[int, float, float] | None:
        return self._visor.pagina_y_punto_pt(pos)

    def _indice_en(
        self, palabras: tuple[PalabraTexto, ...], x: float, y: float
    ) -> int | None:
        idx = seleccion.indice_en_punto(palabras, x, y)
        return idx if idx is not None else seleccion.indice_mas_cercano(palabras, x, y)

    # -- Gestos -------------------------------------------------------------

    def _iniciar_arrastre(self, pagina: int, x: float, y: float) -> None:
        palabras = self._palabras(pagina)
        idx = self._indice_en(palabras, x, y)
        if idx is None:
            self.limpiar()
            return
        self._arrastrando = True
        self._anclaje = idx
        self._fijar_seleccion(pagina, palabras, idx, idx)

    def _extender_arrastre(self, x: float, y: float) -> None:
        if not self._arrastrando or self._sel_pagina < 0:
            return
        palabras = self._palabras(self._sel_pagina)
        idx = seleccion.indice_mas_cercano(palabras, x, y)
        if idx is None:
            return
        inicio, fin = seleccion.rango(self._anclaje, idx)
        self._fijar_seleccion(self._sel_pagina, palabras, inicio, fin)

    def _seleccionar_palabra(self, pagina: int, x: float, y: float) -> None:
        palabras = self._palabras(pagina)
        idx = self._indice_en(palabras, x, y)
        if idx is None:
            return
        inicio, fin = seleccion.indices_palabra(palabras, idx)
        self._fijar_seleccion(pagina, palabras, inicio, fin)

    def _seleccionar_parrafo(self, pagina: int, x: float, y: float) -> None:
        palabras = self._palabras(pagina)
        idx = self._indice_en(palabras, x, y)
        if idx is None:
            return
        inicio, fin = seleccion.indices_parrafo(palabras, idx)
        self._fijar_seleccion(pagina, palabras, inicio, fin)

    def _fijar_seleccion(
        self,
        pagina: int,
        palabras: tuple[PalabraTexto, ...],
        inicio: int,
        fin: int,
    ) -> None:
        self._sel_pagina = pagina
        self._sel_palabras = palabras
        self._sel_inicio = inicio
        self._sel_fin = fin
        self._repintar()

    # -- Pintado ------------------------------------------------------------

    def _repintar(self) -> None:
        escena = self._visor.scene()
        if escena is None:
            return
        for item in self._items:
            if item.scene() is escena:
                escena.removeItem(item)
        self._items.clear()
        if self._sel_inicio < 0 or self._sel_pagina < 0:
            return
        rect_pagina = self._visor.rect_pagina(self._sel_pagina)
        if rect_pagina is None:
            return
        pincel = _pincel_seleccion()
        pluma = QPen(Qt.PenStyle.NoPen)
        for i in range(self._sel_inicio, self._sel_fin + 1):
            r = rect_pdf_a_escena(
                self._sel_palabras[i].rect_pt,
                rect_pagina.left(),
                rect_pagina.top(),
                self._visor.escala,
            )
            item = escena.addRect(QRectF(r.x, r.y, r.ancho, r.alto), pluma, pincel)
            item.setZValue(_Z_SELECCION)
            self._items.append(item)

    # -- Filtro de eventos --------------------------------------------------

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        # Qt puede enrutar eventos al filtro durante la construcción/destrucción,
        # cuando aún no hay visor o su objeto C++ ya se destruyó: se ignoran.
        visor = getattr(self, "_visor", None)
        if visor is None:
            return False
        try:
            tipo = event.type()
            if obj is visor and tipo == QEvent.Type.KeyPress:
                return self._al_teclado(event)
            if obj is visor.viewport() and isinstance(event, QMouseEvent):
                return self._al_raton(tipo, event)
        except RuntimeError:
            return False
        return super().eventFilter(obj, event)

    def _al_teclado(self, event: QEvent) -> bool:
        if (
            isinstance(event, QKeyEvent)
            and event.matches(QKeySequence.StandardKey.Copy)
            and self.texto_seleccionado()
        ):
            self.copiar()
            return True
        return False

    def _al_raton(self, tipo: QEvent.Type, event: QMouseEvent) -> bool:
        if self._documento is None or event.button() not in (
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
        ):
            return False
        pos = event.position().toPoint()
        if tipo == QEvent.Type.MouseButtonPress:
            return self._press(pos, event.timestamp())
        if tipo == QEvent.Type.MouseMove and self._arrastrando:
            destino = self._pagina_y_punto(pos)
            if destino is not None:
                self._extender_arrastre(destino[1], destino[2])
            return False
        if tipo == QEvent.Type.MouseButtonRelease:
            self._arrastrando = False
            return False
        if tipo == QEvent.Type.MouseButtonDblClick:
            destino = self._pagina_y_punto(pos)
            if destino is not None:
                self._seleccionar_palabra(*destino)
            return True
        return False

    def _press(self, pos: QPoint, ms: int) -> bool:
        px, py = pos.x(), pos.y()
        intervalo = QGuiApplication.styleHints().mouseDoubleClickInterval()
        cerca = (
            abs(px - self._ultimo_pos[0]) <= _TOLERANCIA_TRIPLE_PX
            and abs(py - self._ultimo_pos[1]) <= _TOLERANCIA_TRIPLE_PX
        )
        if ms - self._ultimo_click_ms <= intervalo and cerca:
            self._racha = self._racha % 3 + 1
        else:
            self._racha = 1
        self._ultimo_click_ms = ms
        self._ultimo_pos = (float(px), float(py))

        destino = self._pagina_y_punto(pos)
        if destino is None:
            self.limpiar()
            return False
        pagina, x, y = destino
        if self._racha == 3:  # triple clic: párrafo
            self._arrastrando = False
            self._seleccionar_parrafo(pagina, x, y)
            return True
        if self._racha == 2:  # el doble clic lo resuelve el evento DblClick
            return False
        self._iniciar_arrastre(pagina, x, y)
        return False
