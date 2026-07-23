"""Controlador del modo "colocar texto" sobre el visor (Fase 9).

Calca `SignatureLayer`: coloca una previsualización movible/redimensionable del
texto; al confirmar, calcula la página y su rectángulo en puntos PDF, llama al
caso de uso `AnadirTexto` e invalida el render de esa página.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF

from lectorpdf.core.domain.anotaciones import Color, FuenteTexto, TextoNuevo
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.anadir_texto import AnadirTexto
from lectorpdf.ui.forms.coordenadas import RectEscena, rect_escena_a_pdf
from lectorpdf.ui.texto.text_placement_item import TextPlacementItem
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_FRACCION_ANCHO_PAGINA = 0.5


class TextoLayer:
    def __init__(self, visor: ViewerWidget, caso_anadir: AnadirTexto) -> None:
        self._visor = visor
        self._caso = caso_anadir
        self._documento: Documento | None = None
        self._item: TextPlacementItem | None = None
        self._texto = ""
        self._fuente = FuenteTexto.SANS
        self._tamano = 12.0
        self._color: Color = (0.0, 0.0, 0.0)
        visor.escena_reconstruida.connect(self._al_reconstruir_escena)

    def colocando(self) -> bool:
        return self._item is not None

    def iniciar_colocacion(
        self,
        documento: Documento,
        texto: str,
        fuente: FuenteTexto,
        tamano: float,
        color: Color,
    ) -> None:
        self.cancelar()
        self._documento = documento
        self._texto = texto
        self._fuente = fuente
        self._tamano = tamano
        self._color = color

        pagina = self._visor.pagina_actual()
        rect_pagina = self._visor.rect_pagina(pagina)
        ancho = (rect_pagina.width() if rect_pagina else 300.0) * _FRACCION_ANCHO_PAGINA
        alto = max(tamano * self._visor.escala * 2.2, 40.0)

        item = TextPlacementItem(
            texto, fuente, tamano * self._visor.escala, color, ancho, alto
        )
        escena = self._visor.scene()
        if escena is not None:
            escena.addItem(item)
        self._item = item
        self._centrar_en_pagina(item, pagina, ancho, alto)

    def cancelar(self) -> None:
        self._quitar_item()
        self._documento = None
        self._texto = ""

    def confirmar(self) -> int | None:
        """Estampa el texto. Devuelve la página o None si no procede."""
        if self._item is None or self._documento is None:
            return None
        rect_escena = self._item.rect_en_escena()
        pagina = self._visor.pagina_en_punto(rect_escena.center())
        if pagina is None:
            return None
        rect_pagina = self._visor.rect_pagina(pagina)
        if rect_pagina is None:
            return None
        rect_pt = rect_escena_a_pdf(
            RectEscena(
                rect_escena.x(),
                rect_escena.y(),
                rect_escena.width(),
                rect_escena.height(),
            ),
            rect_pagina.left(),
            rect_pagina.top(),
            self._visor.escala,
        )
        texto = TextoNuevo(rect_pt, self._texto, self._fuente, self._tamano, self._color)
        self._caso.ejecutar(self._documento, pagina, texto)
        self._quitar_item()
        self._documento = None
        self._texto = ""
        self._visor.invalidar_pagina(pagina)
        return pagina

    # -- Interno ------------------------------------------------------------

    def _al_reconstruir_escena(self) -> None:
        self._item = None

    def _quitar_item(self) -> None:
        if self._item is not None:
            escena = self._item.scene()
            if escena is not None:
                escena.removeItem(self._item)
            self._item = None

    def _centrar_en_pagina(
        self, item: TextPlacementItem, pagina: int, ancho: float, alto: float
    ) -> None:
        rect_pagina = self._visor.rect_pagina(pagina)
        if rect_pagina is None:
            return
        centro = rect_pagina.center()
        item.setPos(QPointF(centro.x() - ancho / 2, centro.y() - alto / 2))
