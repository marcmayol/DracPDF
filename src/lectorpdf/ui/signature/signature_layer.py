"""Controlador del modo "colocar firma" sobre el visor.

Coloca una previsualización movible de la firma en la escena; al confirmar,
calcula la página bajo la firma y su rectángulo en puntos PDF (inversa de la
transformación de coordenadas), llama al caso de uso EstamparFirma e invalida el
render de esa página para que el estampado aparezca.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPixmap

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.estampar_firma import EstamparFirma
from lectorpdf.ui.forms.coordenadas import RectEscena, rect_escena_a_pdf
from lectorpdf.ui.signature.placement_item import SignaturePlacementItem
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_FRACCION_ANCHO_PAGINA = 0.35  # ancho inicial de la firma respecto a la página


class SignatureLayer:
    def __init__(self, visor: ViewerWidget, caso_estampar: EstamparFirma) -> None:
        self._visor = visor
        self._caso = caso_estampar
        self._documento: Documento | None = None
        self._item: SignaturePlacementItem | None = None
        self._png: bytes = b""
        visor.escena_reconstruida.connect(self._al_reconstruir_escena)

    def colocando(self) -> bool:
        return self._item is not None

    def iniciar_colocacion(self, documento: Documento, imagen_png: bytes) -> None:
        self.cancelar()
        self._documento = documento
        self._png = imagen_png

        pixmap = QPixmap()
        pixmap.loadFromData(imagen_png)  # formato autodetectado por la cabecera

        pagina = self._visor.pagina_actual()
        rect_pagina = self._visor.rect_pagina(pagina)
        ancho = (rect_pagina.width() if rect_pagina else 200.0) * _FRACCION_ANCHO_PAGINA
        proporcion = pixmap.height() / pixmap.width() if pixmap.width() else 0.4
        alto = ancho * proporcion

        item = SignaturePlacementItem(pixmap, ancho, alto)
        escena = self._visor.scene()
        if escena is not None:
            escena.addItem(item)
        self._item = item
        self._centrar_en_pagina(item, pagina, ancho, alto)

    def cancelar(self) -> None:
        self._quitar_item()
        self._documento = None
        self._png = b""

    def confirmar(self) -> int | None:
        """Estampa la firma. Devuelve la página estampada o None si no procede."""
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

        self._caso.ejecutar(self._documento, pagina, rect_pt, self._png)
        self._quitar_item()
        self._documento = None
        self._png = b""
        self._visor.invalidar_pagina(pagina)
        return pagina

    # -- Interno ------------------------------------------------------------

    def _al_reconstruir_escena(self) -> None:
        # La escena se vació (apertura/zoom): el item ya no existe.
        self._item = None

    def _quitar_item(self) -> None:
        if self._item is not None:
            escena = self._item.scene()
            if escena is not None:
                escena.removeItem(self._item)
            self._item = None

    def _centrar_en_pagina(
        self, item: SignaturePlacementItem, pagina: int, ancho: float, alto: float
    ) -> None:
        rect_pagina = self._visor.rect_pagina(pagina)
        if rect_pagina is None:
            return
        centro = rect_pagina.center()
        item.setPos(QPointF(centro.x() - ancho / 2, centro.y() - alto / 2))
