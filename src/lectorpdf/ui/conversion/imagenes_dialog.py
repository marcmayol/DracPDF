"""Diálogo de imágenes → PDF: orden de las páginas y ajuste de página.

El orden de la lista es el orden del PDF: se puede reordenar y quitar imágenes
antes de convertir, porque el selector de ficheros del sistema no garantiza
ningún orden útil.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from lectorpdf.core.domain.conversion import A4, CARTA, AjusteImagen, ConfigPagina

_TAMANOS: dict[str, ConfigPagina] = {"A4": A4, "Carta": CARTA}
_AJUSTES: dict[str, AjusteImagen] = {
    "Cada página, del tamaño de su imagen": AjusteImagen.TAMANO_IMAGEN,
    "Tamaño de página fijo, con márgenes": AjusteImagen.PAGINA_FIJA,
}


class ConversionImagenesDialog(QDialog):
    def __init__(self, rutas: list[Path], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Convertir imágenes a PDF")

        self._lista = QListWidget()
        self._lista.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        for ruta in rutas:
            self._lista.addItem(str(ruta))

        subir = QPushButton("Subir")
        bajar = QPushButton("Bajar")
        quitar = QPushButton("Quitar")
        subir.clicked.connect(lambda: self._mover(-1))
        bajar.clicked.connect(lambda: self._mover(1))
        quitar.clicked.connect(self._quitar)

        botonera = QHBoxLayout()
        for boton in (subir, bajar, quitar):
            botonera.addWidget(boton)
        botonera.addStretch(1)

        self._ajuste = QComboBox()
        self._ajuste.addItems(list(_AJUSTES))
        self._tamano = QComboBox()
        self._tamano.addItems(list(_TAMANOS))
        self._margen = QSpinBox()
        self._margen.setRange(0, 50)
        self._margen.setValue(20)
        self._margen.setSuffix(" mm")

        opciones = QFormLayout()
        opciones.addRow("Páginas:", self._ajuste)
        opciones.addRow("Tamaño de página:", self._tamano)
        opciones.addRow("Margen:", self._margen)

        self._botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._botones.accepted.connect(self.accept)
        self._botones.rejected.connect(self.reject)

        caja = QVBoxLayout(self)
        caja.addWidget(QLabel("Una imagen por página, en este orden:"))
        caja.addWidget(self._lista)
        caja.addLayout(botonera)
        caja.addLayout(opciones)
        caja.addWidget(self._botones)

        self._ajuste.currentTextChanged.connect(self._sincronizar_opciones)
        self._lista.model().rowsRemoved.connect(self._sincronizar_aceptar)
        self._sincronizar_opciones()
        self._sincronizar_aceptar()

    def rutas(self) -> list[Path]:
        """Imágenes en el orden elegido por el usuario."""
        return [
            Path(self._lista.item(fila).text()) for fila in range(self._lista.count())
        ]

    def ajuste(self) -> AjusteImagen:
        return _AJUSTES[self._ajuste.currentText()]

    def config(self) -> ConfigPagina:
        base = _TAMANOS[self._tamano.currentText()]
        return ConfigPagina(
            ancho_mm=base.ancho_mm,
            alto_mm=base.alto_mm,
            margen_mm=float(self._margen.value()),
        )

    # -- Interno ------------------------------------------------------------

    def _sincronizar_opciones(self) -> None:
        """Tamaño y margen solo pintan algo con la página fija."""
        fija = self.ajuste() is AjusteImagen.PAGINA_FIJA
        self._tamano.setEnabled(fija)
        self._margen.setEnabled(fija)

    def _sincronizar_aceptar(self) -> None:
        boton = self._botones.button(QDialogButtonBox.StandardButton.Ok)
        if boton is not None:
            boton.setEnabled(self._lista.count() > 0)

    def _mover(self, salto: int) -> None:
        fila = self._lista.currentRow()
        destino = fila + salto
        if fila < 0 or destino < 0 or destino >= self._lista.count():
            return
        item = self._lista.takeItem(fila)
        self._lista.insertItem(destino, item)
        self._lista.setCurrentRow(destino)

    def _quitar(self) -> None:
        for item in self._lista.selectedItems():
            self._lista.takeItem(self._lista.row(item))
        self._sincronizar_aceptar()
