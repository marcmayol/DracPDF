"""Diálogo de PDF → tablas: estrategia, recuento previo y formato.

Un PDF no sabe qué es una tabla: hay que deducirla, y ninguna deducción acierta
siempre. Por eso aquí se ve QUÉ se ha encontrado antes de escribir ficheros, y
se puede cambiar de estrategia y volver a mirar.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from lectorpdf.core.domain.tablas import (
    EstrategiaTablas,
    FormatoTabla,
    TablaDetectada,
)

_ESTRATEGIAS: dict[str, EstrategiaTablas] = {
    "Tablas con líneas (fiable)": EstrategiaTablas.LINEAS,
    "Deducir por alineación del texto (aproximado)": EstrategiaTablas.TEXTO,
}
_FORMATOS: dict[str, FormatoTabla] = {
    "CSV (un fichero por tabla)": FormatoTabla.CSV,
    "Excel (un libro con una hoja por tabla)": FormatoTabla.XLSX,
}
_AVISO_APROXIMADO = (
    "Sin líneas que seguir, se deducen las columnas de la posición del texto: "
    "puede trocear en celdas párrafos que no son tablas. Revisa el resultado."
)


class ConversionTablasDialog(QDialog):
    def __init__(
        self,
        detectar: Callable[[EstrategiaTablas], Sequence[TablaDetectada]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Convertir tablas")
        self._detectar = detectar

        self._estrategia = QComboBox()
        self._estrategia.addItems(list(_ESTRATEGIAS))
        self._formato = QComboBox()
        self._formato.addItems(list(_FORMATOS))

        self._resumen = QLabel("")
        self._resumen.setWordWrap(True)
        self._lista = QListWidget()

        opciones = QFormLayout()
        opciones.addRow("Buscar:", self._estrategia)
        opciones.addRow("Guardar como:", self._formato)

        self._botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._botones.accepted.connect(self.accept)
        self._botones.rejected.connect(self.reject)

        caja = QVBoxLayout(self)
        caja.addLayout(opciones)
        caja.addWidget(self._resumen)
        caja.addWidget(self._lista)
        caja.addWidget(self._botones)

        self._estrategia.currentTextChanged.connect(self._buscar)
        self._buscar()

    def estrategia(self) -> EstrategiaTablas:
        return _ESTRATEGIAS[self._estrategia.currentText()]

    def formato(self) -> FormatoTabla:
        return _FORMATOS[self._formato.currentText()]

    def detectadas(self) -> tuple[TablaDetectada, ...]:
        return self._detectadas

    # -- Interno ------------------------------------------------------------

    def _buscar(self) -> None:
        estrategia = self.estrategia()
        self._detectadas = tuple(self._detectar(estrategia))
        self._lista.clear()
        for tabla in self._detectadas:
            self._lista.addItem(
                f"Página {tabla.pagina + 1}, tabla {tabla.indice + 1}: "
                f"{tabla.filas} filas × {tabla.columnas} columnas"
            )
        if not self._detectadas:
            self._resumen.setText(
                "No se ha encontrado ninguna tabla."
                + (
                    ""
                    if estrategia.es_aproximada
                    else " Si la tabla no tiene líneas dibujadas, prueba a deducirla "
                    "por la alineación del texto."
                )
            )
        else:
            paginas = len({t.pagina for t in self._detectadas})
            self._resumen.setText(
                f"{len(self._detectadas)} tabla(s) en {paginas} página(s)."
                + (f" {_AVISO_APROXIMADO}" if estrategia.es_aproximada else "")
            )
        boton = self._botones.button(QDialogButtonBox.StandardButton.Ok)
        if boton is not None:
            boton.setEnabled(bool(self._detectadas))
