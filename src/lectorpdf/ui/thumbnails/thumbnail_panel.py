"""Panel lateral de miniaturas con renderizado perezoso.

Las miniaturas se generan solo cuando su fila entra en el área visible del
panel, para no renderizar cientos de páginas al abrir el documento.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.viewer.imagen import qpixmap_desde

ANCHO_MINIATURA_PT_A_PX = 120  # ancho objetivo de la miniatura en píxeles
_ROL_INDICE = int(Qt.ItemDataRole.UserRole)


class ThumbnailPanel(QListWidget):
    """Lista de miniaturas; emite `pagina_seleccionada` al elegir una."""

    pagina_seleccionada = Signal(int)

    def __init__(self, caso_render: RenderizarPagina) -> None:
        super().__init__()
        self._caso_render = caso_render
        self._documento: Documento | None = None
        self._renderizadas: set[int] = set()
        self._sincronizando = False

        self.setIconSize(QSize(ANCHO_MINIATURA_PT_A_PX, int(ANCHO_MINIATURA_PT_A_PX * 1.5)))
        self.setSpacing(4)
        self.setUniformItemSizes(False)
        self.setMaximumWidth(ANCHO_MINIATURA_PT_A_PX + 70)

        self.currentRowChanged.connect(self._on_fila_cambiada)
        scrollbar = self.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.valueChanged.connect(lambda _: self._render_visibles())

    def set_documento(self, documento: Documento) -> None:
        self._documento = documento
        self._renderizadas.clear()
        self.clear()
        for pagina in documento.paginas:
            item = QListWidgetItem(str(pagina.indice + 1))
            item.setData(_ROL_INDICE, pagina.indice)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            # Reserva espacio para que el scroll conozca el tamaño sin renderizar.
            alto = int(pagina.alto_pt / pagina.ancho_pt * ANCHO_MINIATURA_PT_A_PX)
            item.setSizeHint(QSize(ANCHO_MINIATURA_PT_A_PX + 40, alto + 24))
            self.addItem(item)
        self._render_visibles()

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

    # -- Interno ------------------------------------------------------------

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
