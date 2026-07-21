"""Control de navegación de página de la toolbar: ◀ [n / total] ▶.

Según la maqueta Ladón: flechas anterior/siguiente flanqueando un campo con el
número de página editable y el total. Escribir un número y confirmar navega.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QToolButton,
    QWidget,
)

from lectorpdf.ui.theme.iconos import icono


class ControlPagina(QWidget):
    #: Página pedida al escribir en el campo (0-based).
    pagina_pedida = Signal(int)
    anterior = Signal()
    siguiente = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._total = 0

        self._prev = QToolButton()
        self._prev.setToolTip("Página anterior")
        self._prev.clicked.connect(self.anterior)
        self._next = QToolButton()
        self._next.setToolTip("Página siguiente")
        self._next.clicked.connect(self.siguiente)

        self._campo = QLineEdit()
        self._campo.setObjectName("campoPagina")
        self._campo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._campo.setFixedWidth(44)  # cabe números de página de 3-4 cifras
        self._campo.setValidator(QIntValidator(1, 1, self))
        self._campo.editingFinished.connect(self._al_editar)

        self._etiqueta_total = QLabel("/ 0")
        self._etiqueta_total.setObjectName("totalPagina")

        disposicion = QHBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(4)
        disposicion.addWidget(self._prev)
        disposicion.addWidget(self._campo)
        disposicion.addWidget(self._etiqueta_total)
        disposicion.addWidget(self._next)

    def recolorear(self, color_hex: str) -> None:
        self._prev.setIcon(icono("page-prev", color_hex))
        self._next.setIcon(icono("page-next", color_hex))

    def set_estado(self, pagina: int, total: int) -> None:
        """Refleja la página actual (0-based) y el total."""
        self._total = total
        self._campo.setValidator(QIntValidator(1, max(1, total), self))
        if not self._campo.hasFocus():
            self._campo.setText(str(pagina + 1) if total else "")
        self._etiqueta_total.setText(f"/ {total}")
        habilitado = total > 0
        for w in (self._prev, self._next, self._campo):
            w.setEnabled(habilitado)

    def _al_editar(self) -> None:
        texto = self._campo.text().strip()
        if texto and self._total:
            pagina = max(1, min(int(texto), self._total)) - 1
            self.pagina_pedida.emit(pagina)
