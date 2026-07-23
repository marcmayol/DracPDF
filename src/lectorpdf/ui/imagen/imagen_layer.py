"""Controlador del modo "colocar imagen" sobre el visor (Fase 9, Parte C).

Calca `TextoLayer`: coloca una previsualización movible/redimensionable de la
imagen; al confirmar, calcula la página y su rectángulo en puntos PDF, llama al
caso de uso `AnadirImagen` e invalida el render de esa página.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPixmap

from lectorpdf.core.domain.anotaciones import ImagenNueva
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.anadir_imagen import AnadirImagen
from lectorpdf.ui.forms.coordenadas import RectEscena, rect_escena_a_pdf
from lectorpdf.ui.imagen.image_placement_item import ImagePlacementItem
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_FRACCION_ANCHO_PAGINA = 0.4


class ImagenLayer:
    def __init__(self, visor: ViewerWidget, caso_anadir: AnadirImagen) -> None:
        self._visor = visor
        self._caso = caso_anadir
        self._documento: Documento | None = None
        self._item: ImagePlacementItem | None = None
        self._ruta: Path | None = None
        self._conservar = True
        visor.escena_reconstruida.connect(self._al_reconstruir_escena)

    def colocando(self) -> bool:
        return self._item is not None

    def iniciar_colocacion(
        self, documento: Documento, ruta: Path, conservar_proporcion: bool = True
    ) -> bool:
        """Arranca la colocación. Devuelve False si la imagen no se pudo cargar."""
        self.cancelar()
        pixmap = QPixmap(str(ruta))
        if pixmap.isNull():
            return False
        self._documento = documento
        self._ruta = ruta
        self._conservar = conservar_proporcion

        pagina = self._visor.pagina_actual()
        rect_pagina = self._visor.rect_pagina(pagina)
        ancho = (rect_pagina.width() if rect_pagina else 300.0) * _FRACCION_ANCHO_PAGINA

        item = ImagePlacementItem(pixmap, ancho, conservar_proporcion)
        escena = self._visor.scene()
        if escena is not None:
            escena.addItem(item)
        self._item = item
        self._centrar_en_pagina(item, pagina)
        return True

    def cancelar(self) -> None:
        self._quitar_item()
        self._documento = None
        self._ruta = None

    def confirmar(self) -> int | None:
        """Inserta la imagen. Devuelve la página o None si no procede."""
        if self._item is None or self._documento is None or self._ruta is None:
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
        imagen = ImagenNueva(rect_pt, self._ruta, self._conservar)
        self._caso.ejecutar(self._documento, pagina, imagen)
        self._quitar_item()
        self._documento = None
        self._ruta = None
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

    def _centrar_en_pagina(self, item: ImagePlacementItem, pagina: int) -> None:
        rect_pagina = self._visor.rect_pagina(pagina)
        if rect_pagina is None:
            return
        rect_item = item.rect_en_escena()
        centro = rect_pagina.center()
        item.setPos(
            QPointF(
                centro.x() - rect_item.width() / 2,
                centro.y() - rect_item.height() / 2,
            )
        )
