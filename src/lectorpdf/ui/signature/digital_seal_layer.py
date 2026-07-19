"""Colocación del sello de firma digital sobre la página, antes de firmar.

Reutiliza el item movible/redimensionable de la Fase 3 para que el usuario elija
la posición; al confirmar calcula la página y el rect en puntos PDF, llama a
FirmarDigitalmente y re-renderiza el documento (que la firma ya cambió en disco).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap

from lectorpdf.core.domain.firma_digital import ConfigFirma, CredencialFirma
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.firmar_digitalmente import FirmarDigitalmente
from lectorpdf.ui.forms.coordenadas import RectEscena, rect_escena_a_pdf
from lectorpdf.ui.signature.placement_item import SignaturePlacementItem
from lectorpdf.ui.theme.tokens import OVERLAY_FIRMA
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_FRACCION_ANCHO = 0.4


class DigitalSealLayer:
    def __init__(self, visor: ViewerWidget, caso_firmar: FirmarDigitalmente) -> None:
        self._visor = visor
        self._caso = caso_firmar
        self._documento: Documento | None = None
        self._credencial: CredencialFirma | None = None
        self._razon: str | None = None
        self._item: SignaturePlacementItem | None = None
        visor.escena_reconstruida.connect(self._olvidar_item)

    def colocando(self) -> bool:
        return self._item is not None

    def iniciar_colocacion(
        self, documento: Documento, credencial: CredencialFirma, razon: str | None
    ) -> None:
        self.cancelar()
        self._documento = documento
        self._credencial = credencial
        self._razon = razon

        pagina = self._visor.pagina_actual()
        rect_pagina = self._visor.rect_pagina(pagina)
        ancho = (rect_pagina.width() if rect_pagina else 200.0) * _FRACCION_ANCHO
        alto = ancho * 0.32
        item = SignaturePlacementItem(_placeholder(int(ancho), int(alto)), ancho, alto)
        escena = self._visor.scene()
        if escena is not None:
            escena.addItem(item)
        self._item = item
        if rect_pagina is not None:
            centro = rect_pagina.center()
            item.setPos(QPointF(centro.x() - ancho / 2, centro.y() - alto / 2))

    def cancelar(self) -> None:
        self._quitar_item()
        self._documento = None
        self._credencial = None
        self._razon = None

    def confirmar(self) -> int | None:
        if self._item is None or self._documento is None or self._credencial is None:
            return None
        rect_escena = self._item.rect_en_escena()
        pagina = self._visor.pagina_en_punto(rect_escena.center())
        rect_pagina = self._visor.rect_pagina(pagina) if pagina is not None else None
        if pagina is None or rect_pagina is None:
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
        config = ConfigFirma(pagina=pagina, rect_pt=rect_pt, razon=self._razon)
        documento = self._documento

        self._caso.ejecutar(documento, config, self._credencial)
        self._quitar_item()
        self._documento = None
        self._credencial = None
        # La firma cambió el fichero en disco: re-renderizar para ver el sello.
        for indice in range(documento.num_paginas):
            self._visor.invalidar_pagina(indice)
        return pagina

    # -- Interno ------------------------------------------------------------

    def _olvidar_item(self) -> None:
        self._item = None

    def _quitar_item(self) -> None:
        if self._item is not None:
            escena = self._item.scene()
            if escena is not None:
                escena.removeItem(self._item)
            self._item = None


def _placeholder(ancho: int, alto: int) -> QPixmap:
    relleno = QColor(OVERLAY_FIRMA)
    relleno.setAlpha(30)
    pixmap = QPixmap(max(ancho, 1), max(alto, 1))
    pixmap.fill(relleno)
    pintor = QPainter(pixmap)
    pintor.setPen(QPen(QColor(OVERLAY_FIRMA), 1, Qt.PenStyle.DashLine))
    pintor.drawRect(0, 0, pixmap.width() - 1, pixmap.height() - 1)
    pintor.drawText(
        QRectF(0, 0, pixmap.width(), pixmap.height()),
        int(Qt.AlignmentFlag.AlignCenter),
        "FIRMA DIGITAL",
    )
    pintor.end()
    return pixmap
