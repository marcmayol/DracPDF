"""Panel lateral de miniaturas con renderizado perezoso.

Las miniaturas se generan solo cuando su fila entra en el área visible del
panel, para no renderizar cientos de páginas al abrir el documento.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QResizeEvent
from PySide6.QtWidgets import QListView, QListWidget, QListWidgetItem, QMenu

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.viewer.imagen import qpixmap_desde

ANCHO_MINIATURA_PT_A_PX = 120  # ancho objetivo de la miniatura en píxeles
_ROL_INDICE = int(Qt.ItemDataRole.UserRole)


class ThumbnailPanel(QListWidget):
    """Lista de miniaturas; emite `pagina_seleccionada` al elegir una y señales
    de organización (rotar/eliminar/mover) desde su menú contextual."""

    pagina_seleccionada = Signal(int)
    rotar_solicitado = Signal(int, int)  # indice, grados
    eliminar_solicitado = Signal(int)  # indice
    mover_solicitado = Signal(int, int)  # origen, destino

    def __init__(self, caso_render: RenderizarPagina) -> None:
        super().__init__()
        self._caso_render = caso_render
        self._documento: Documento | None = None
        self._renderizadas: set[int] = set()
        self._sincronizando = False

        self.setIconSize(QSize(ANCHO_MINIATURA_PT_A_PX, int(ANCHO_MINIATURA_PT_A_PX * 1.5)))
        self.setSpacing(4)
        self.setUniformItemSizes(False)
        # Columna única con la miniatura centrada (IconMode: icono arriba, número
        # debajo). La lista ocupa todo el ancho del dock: sin franja lateral que
        # deje asomar el contenedor. El ancho de cada item se ajusta al viewport.
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setFlow(QListView.Flow.TopToBottom)
        self.setWrapping(False)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)

        self.currentRowChanged.connect(self._on_fila_cambiada)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu_contextual)
        scrollbar = self.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.valueChanged.connect(lambda _: self._render_visibles())

    def set_documento(self, documento: Documento) -> None:
        self._documento = documento
        self._renderizadas.clear()
        self.clear()
        ancho = self._ancho_item()
        alto = self._alto_item()
        for pagina in documento.paginas:
            item = QListWidgetItem(str(pagina.indice + 1))
            item.setData(_ROL_INDICE, pagina.indice)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            # Reserva espacio para que el scroll conozca el tamaño sin renderizar.
            item.setSizeHint(QSize(ancho, alto))
            self.addItem(item)
        self._render_visibles()

    def _alto_item(self) -> int:
        """Alto uniforme del item: caja del icono + hueco para el número."""
        return self.iconSize().height() + 26

    def _ancho_item(self) -> int:
        """Ancho de cada item = ancho del viewport (miniatura centrada), con un
        mínimo por si aún no se ha dispuesto el widget."""
        return max(self.viewport().width(), ANCHO_MINIATURA_PT_A_PX + 40)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        ancho = self._ancho_item()
        alto = self._alto_item()
        for fila in range(self.count()):
            item = self.item(fila)
            if item is not None:
                item.setSizeHint(QSize(ancho, alto))

    def limpiar(self) -> None:
        """Vacía el panel (pestaña sin documento)."""
        self._documento = None
        self._renderizadas.clear()
        self.clear()

    def seleccionar_pagina(self, indice: int) -> None:
        """Sincroniza la selección con el visor sin re-emitir la señal."""
        if indice < 0 or indice >= self.count():
            return
        self._sincronizando = True
        self.setCurrentRow(indice)
        item = self.item(indice)
        if item is not None:
            self.scrollToItem(item)
        self._sincronizando = False
        self._render_visibles()

    def menu_organizacion(self, indice: int) -> QMenu:
        """Construye el menú contextual de organización para `indice` (testable)."""
        menu = QMenu(self)
        menu.addAction(
            "Rotar a la derecha", lambda: self.rotar_solicitado.emit(indice, 90)
        )
        menu.addAction(
            "Rotar a la izquierda", lambda: self.rotar_solicitado.emit(indice, -90)
        )
        menu.addSeparator()
        if indice > 0:
            menu.addAction("Subir", lambda: self.mover_solicitado.emit(indice, indice - 1))
        if indice < self.count() - 1:
            menu.addAction("Bajar", lambda: self.mover_solicitado.emit(indice, indice + 1))
        menu.addSeparator()
        menu.addAction(
            "Eliminar página", lambda: self.eliminar_solicitado.emit(indice)
        )
        return menu

    # -- Interno ------------------------------------------------------------

    def _menu_contextual(self, pos: QPoint) -> None:
        item = self.itemAt(pos)
        if item is None:
            return
        indice = int(item.data(_ROL_INDICE))
        self.menu_organizacion(indice).exec(self.mapToGlobal(pos))

    def _on_fila_cambiada(self, fila: int) -> None:
        if self._sincronizando or fila < 0:
            return
        item = self.item(fila)
        if item is not None:
            self.pagina_seleccionada.emit(int(item.data(_ROL_INDICE)))

    def _render_visibles(self) -> None:
        if self._documento is None:
            return
        area_visible = self.viewport().rect()
        for fila in range(self.count()):
            item = self.item(fila)
            if item is None:
                continue
            indice = int(item.data(_ROL_INDICE))
            if indice in self._renderizadas:
                continue
            if self.visualItemRect(item).intersects(area_visible):
                self._render_miniatura(item, indice)

    def _render_miniatura(self, item: QListWidgetItem, indice: int) -> None:
        assert self._documento is not None
        pagina = self._documento.paginas[indice]
        escala = ANCHO_MINIATURA_PT_A_PX / pagina.ancho_pt
        imagen = self._caso_render.ejecutar(self._documento, indice, escala)
        item.setIcon(QIcon(qpixmap_desde(imagen)))
        self._renderizadas.add(indice)

    def miniaturas_renderizadas(self) -> set[int]:
        """Índices con miniatura ya generada (para tests/diagnóstico)."""
        return set(self._renderizadas)
