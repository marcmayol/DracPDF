"""Modo "seleccionar imagen para eliminar" (Fase 9, Parte C).

Mientras está activo, filtra el ratón del visor: al pasar por encima de una
imagen la resalta con su contorno EXACTO (`get_image_rects`), y al hacer clic la
elige y avisa a la ventana (que confirma —con los avisos de imagen en varias
páginas o que cubre la página— antes de borrarla). Esc o clic en vacío cancela.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, QPoint, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPen
from PySide6.QtWidgets import QGraphicsRectItem

from lectorpdf.core.domain.anotaciones import ImagenEnPagina
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.eliminar_imagen import EliminarImagen
from lectorpdf.ui.forms.coordenadas import rect_pdf_a_escena
from lectorpdf.ui.theme import tokens
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_Z_BORRADO = 3.5  # por encima de todo, para que el contorno se vea


class BorrarImagenLayer(QObject):
    def __init__(self, visor: ViewerWidget, caso: EliminarImagen) -> None:
        super().__init__()
        self._visor = visor
        self._caso = caso
        self._documento: Documento | None = None
        self._activo = False
        self._al_elegir: Callable[[int, ImagenEnPagina], None] | None = None
        self._hover: ImagenEnPagina | None = None
        self._items: list[QGraphicsRectItem] = []
        visor.viewport().installEventFilter(self)
        visor.escena_reconstruida.connect(self._repintar)

    def activo(self) -> bool:
        return self._activo

    def iniciar(
        self, documento: Documento, al_elegir: Callable[[int, ImagenEnPagina], None]
    ) -> None:
        self._documento = documento
        self._al_elegir = al_elegir
        self._activo = True
        self._hover = None
        self._visor.viewport().setMouseTracking(True)

    def cancelar(self) -> None:
        self._activo = False
        self._hover = None
        self._al_elegir = None
        self._repintar()

    # -- Pintado del contorno de la imagen bajo el ratón --------------------

    def _repintar(self) -> None:
        escena = self._visor.scene()
        if escena is None:
            return
        for item in self._items:
            if item.scene() is escena:
                escena.removeItem(item)
        self._items.clear()
        if not self._activo or self._hover is None:
            return
        pagina = self._visor.pagina_actual()
        rect_pagina = self._visor.rect_pagina(pagina)
        if rect_pagina is None:
            return
        r = rect_pdf_a_escena(
            self._hover.rect_pt,
            rect_pagina.left(),
            rect_pagina.top(),
            self._visor.escala,
        )
        color = QColor(tokens.OVERLAY_FIRMA)
        relleno = QColor(color)
        relleno.setAlpha(60)
        item = escena.addRect(
            QRectF(r.x, r.y, r.ancho, r.alto), QPen(color, 2.0), QBrush(relleno)
        )
        item.setZValue(_Z_BORRADO)
        self._items.append(item)

    # -- Filtro de eventos --------------------------------------------------

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        visor = getattr(self, "_visor", None)
        if visor is None or not self._activo or self._documento is None:
            return False
        try:
            if obj is visor.viewport() and isinstance(event, QMouseEvent):
                return self._al_raton(event.type(), event)
        except RuntimeError:
            return False
        return super().eventFilter(obj, event)

    def _al_raton(self, tipo: QEvent.Type, event: QMouseEvent) -> bool:
        pos = event.position().toPoint()
        if tipo == QEvent.Type.MouseMove:
            self._actualizar_hover(pos)
            return False
        if (
            tipo == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            return self._elegir(pos)
        # Consumir doble clic/soltar para no arrastrar selección en este modo.
        return tipo in (
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseButtonDblClick,
        )

    def _imagen_bajo(self, pos: QPoint) -> tuple[int, ImagenEnPagina] | None:
        destino = self._visor.pagina_y_punto_pt(pos)
        if destino is None or self._documento is None:
            return None
        pagina, x, y = destino
        img = self._caso.imagen_en(self._documento, pagina, x, y)
        return (pagina, img) if img is not None else None

    def _actualizar_hover(self, pos: QPoint) -> None:
        encontrada = self._imagen_bajo(pos)
        nueva = encontrada[1] if encontrada else None
        if nueva != self._hover:
            self._hover = nueva
            self._repintar()

    def _elegir(self, pos: QPoint) -> bool:
        encontrada = self._imagen_bajo(pos)
        if encontrada is None or self._al_elegir is None:
            return False
        pagina, img = encontrada
        self._al_elegir(pagina, img)
        return True
