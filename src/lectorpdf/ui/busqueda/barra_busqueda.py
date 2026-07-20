"""Barra de búsqueda (Ctrl+F): campo, distinguir mayúsculas, contador y navegación.

Widget delgado y sin lógica de negocio: emite señales y muestra el contador. La
ventana principal la conecta al caso de uso (que corre en un hilo) y le devuelve
el número de coincidencias y la posición activa.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QToolButton,
    QWidget,
)

from lectorpdf.ui.theme.iconos import icono


class BarraBusqueda(QWidget):
    #: (término, distinguir mayúsculas). La ventana decide si es búsqueda nueva.
    buscar = Signal(str, bool)
    siguiente = Signal()
    anterior = Signal()
    cerrada = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("barraBusqueda")

        self._campo = QLineEdit()
        self._campo.setPlaceholderText("Buscar en el documento…")
        self._campo.setClearButtonEnabled(True)

        self._btn_case = QToolButton()
        self._btn_case.setText("Aa")
        self._btn_case.setCheckable(True)
        self._btn_case.setToolTip("Distinguir mayúsculas y minúsculas")

        self._contador = QLabel("")
        self._contador.setObjectName("contadorBusqueda")

        self._btn_prev = QToolButton()
        self._btn_prev.setToolTip("Anterior (Mayús+F3)")
        self._btn_next = QToolButton()
        self._btn_next.setToolTip("Siguiente (F3)")
        self._btn_cerrar = QToolButton()
        self._btn_cerrar.setText("✕")
        self._btn_cerrar.setToolTip("Cerrar (Esc)")

        disposicion = QHBoxLayout(self)
        disposicion.setContentsMargins(8, 4, 8, 4)
        disposicion.setSpacing(4)
        disposicion.addWidget(self._campo, 1)
        disposicion.addWidget(self._btn_case)
        disposicion.addWidget(self._contador)
        disposicion.addWidget(self._btn_prev)
        disposicion.addWidget(self._btn_next)
        disposicion.addWidget(self._btn_cerrar)

        self._campo.returnPressed.connect(self._emitir_buscar)
        self._btn_case.toggled.connect(lambda _: self._emitir_buscar())
        self._btn_prev.clicked.connect(self.anterior)
        self._btn_next.clicked.connect(self.siguiente)
        self._btn_cerrar.clicked.connect(self.cerrada)

        self.recolorear("#E9EBF0")

    def recolorear(self, color_hex: str) -> None:
        self._btn_prev.setIcon(icono("page-prev", color_hex))
        self._btn_next.setIcon(icono("page-next", color_hex))

    # -- API para la ventana ------------------------------------------------

    def activar(self, texto_inicial: str = "") -> None:
        self.show()
        if texto_inicial:
            self._campo.setText(texto_inicial)
        self._campo.setFocus()
        self._campo.selectAll()

    def texto(self) -> str:
        return self._campo.text()

    def coincidir_mayusculas(self) -> bool:
        return self._btn_case.isChecked()

    def mostrar_contador(self, actual: int, total: int) -> None:
        if total <= 0:
            self._contador.setText("Sin resultados" if self.texto() else "")
        else:
            self._contador.setText(f"{actual} de {total}")

    # -- Eventos ------------------------------------------------------------

    def _emitir_buscar(self) -> None:
        self.buscar.emit(self._campo.text(), self._btn_case.isChecked())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cerrada.emit()
            event.accept()
            return
        super().keyPressEvent(event)
