"""Capa de enlaces clicables sobre el visor.

Filtra los eventos de ratón del viewport: al pasar sobre un enlace muestra el
cursor de mano y, al pulsarlo, emite navegación interna (a otra página) o la
apertura externa (una URL). No abre diálogos ni el navegador: eso lo decide la
ventana, que confirma antes de abrir nada externo. Se instala DESPUÉS de la capa
de selección para tener prioridad (Qt llama los filtros en orden inverso).
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent

from lectorpdf.core.domain.contenido import Enlace
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.obtener_enlaces import ObtenerEnlaces
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget


class EnlacesLayer(QObject):
    #: Enlace interno pulsado: página destino (0-based).
    navegar_interno = Signal(int)
    #: Enlace externo pulsado: URI (la ventana confirma antes de abrir).
    abrir_externo = Signal(str)

    def __init__(self, visor: ViewerWidget, caso_enlaces: ObtenerEnlaces) -> None:
        super().__init__()
        self._visor = visor
        self._caso = caso_enlaces
        self._documento: Documento | None = None
        self._cache: dict[int, tuple[Enlace, ...]] = {}
        visor.viewport().installEventFilter(self)

    def set_documento(self, documento: Documento | None) -> None:
        self._documento = documento
        self._cache.clear()

    # -- Enlaces por página (con caché) -------------------------------------

    def _enlaces(self, pagina: int) -> tuple[Enlace, ...]:
        if self._documento is None:
            return ()
        if pagina not in self._cache:
            self._cache[pagina] = self._caso.ejecutar(self._documento, pagina)
        return self._cache[pagina]

    def enlace_en(self, pagina: int, x: float, y: float) -> Enlace | None:
        for enlace in self._enlaces(pagina):
            r = enlace.rect_pt
            if r.x0 <= x <= r.x1 and r.y0 <= y <= r.y1:
                return enlace
        return None

    def _activar(self, enlace: Enlace) -> None:
        if enlace.uri is not None:
            self.abrir_externo.emit(enlace.uri)
        elif enlace.pagina_destino is not None:
            self.navegar_interno.emit(enlace.pagina_destino)

    # -- Filtro de eventos --------------------------------------------------

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        visor = getattr(self, "_visor", None)
        if visor is None or self._documento is None:
            return False
        try:
            if obj is not visor.viewport() or not isinstance(event, QMouseEvent):
                return super().eventFilter(obj, event)
            pos = event.position().toPoint()
            tipo = event.type()
            if tipo == QEvent.Type.MouseMove:
                self._actualizar_cursor(pos)
                return False
            if (
                tipo == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                enlace = self._enlace_en_pos(pos)
                if enlace is not None:
                    self._activar(enlace)
                    return True  # consume: no inicia selección
        except RuntimeError:
            return False
        return False

    def _enlace_en_pos(self, pos: QPoint) -> Enlace | None:
        destino = self._visor.pagina_y_punto_pt(pos)
        if destino is None:
            return None
        return self.enlace_en(*destino)

    def _actualizar_cursor(self, pos: QPoint) -> None:
        sobre_enlace = self._enlace_en_pos(pos) is not None
        viewport = self._visor.viewport()
        if viewport is None:
            return
        if sobre_enlace:
            viewport.setCursor(Qt.CursorShape.PointingHandCursor)
        elif viewport.cursor().shape() == Qt.CursorShape.PointingHandCursor:
            viewport.unsetCursor()
