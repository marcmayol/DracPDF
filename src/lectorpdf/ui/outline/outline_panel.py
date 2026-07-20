"""Panel de índice (outline): árbol de marcadores que navega a su página.

Construye un QTreeWidget a partir de la lista plana de entradas (nivel, título,
página) del documento. Al pulsar una entrada con destino, emite su página.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from lectorpdf.core.domain.contenido import EntradaIndice

_ROL_PAGINA = Qt.ItemDataRole.UserRole


class OutlinePanel(QTreeWidget):
    #: Página (0-based) de la entrada pulsada (solo si tiene destino).
    pagina_seleccionada = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setColumnCount(1)
        self.itemClicked.connect(self._al_pulsar)

    def set_entradas(self, entradas: tuple[EntradaIndice, ...]) -> bool:
        """Reconstruye el árbol. Devuelve True si hay al menos una entrada."""
        self.clear()
        # Pila de (nivel, item) para colgar cada entrada de su ascendiente.
        pila: list[tuple[int, QTreeWidgetItem]] = []
        for entrada in entradas:
            while pila and pila[-1][0] >= entrada.nivel:
                pila.pop()
            item = QTreeWidgetItem([entrada.titulo])
            item.setData(0, _ROL_PAGINA, entrada.pagina)
            if pila:
                pila[-1][1].addChild(item)
            else:
                self.addTopLevelItem(item)
            pila.append((entrada.nivel, item))
        self.expandAll()
        return bool(entradas)

    def _al_pulsar(self, item: QTreeWidgetItem, columna: int) -> None:
        pagina = item.data(0, _ROL_PAGINA)
        if isinstance(pagina, int) and pagina >= 0:
            self.pagina_seleccionada.emit(pagina)
