"""Diálogo de PDF → imágenes: formato, resolución y calidad.

La calidad solo existe en los formatos con pérdida, y la resolución no pinta
nada en SVG (es vectorial): ambos campos se deshabilitan cuando no aplican, en
vez de aceptar un valor que se ignoraría en silencio.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QWidget,
)

from lectorpdf.core.domain.conversion import CALIDAD_POR_DEFECTO, FormatoImagen
from lectorpdf.core.use_cases.exportar_imagenes import DPI_POR_DEFECTO

_FORMATOS: dict[str, FormatoImagen] = {
    "PNG (sin pérdida)": FormatoImagen.PNG,
    "JPEG (más ligero)": FormatoImagen.JPEG,
    "WEBP (más ligero aún)": FormatoImagen.WEBP,
    "TIFF (un solo fichero con todas las páginas)": FormatoImagen.TIFF,
    "SVG (vectorial, escala sin pixelar)": FormatoImagen.SVG,
}


class ConversionImagenesSalidaDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Convertir a imágenes")

        self._formato = QComboBox()
        self._formato.addItems(list(_FORMATOS))
        self._dpi = QSpinBox()
        self._dpi.setRange(30, 600)
        self._dpi.setValue(DPI_POR_DEFECTO)
        self._dpi.setSuffix(" DPI")
        self._calidad = QSpinBox()
        self._calidad.setRange(1, 100)
        self._calidad.setValue(CALIDAD_POR_DEFECTO)
        self._calidad.setSuffix(" %")

        self._nota = QLabel("")
        self._nota.setWordWrap(True)

        form = QFormLayout(self)
        form.addRow("Formato:", self._formato)
        form.addRow("Resolución:", self._dpi)
        form.addRow("Calidad:", self._calidad)
        form.addRow(self._nota)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        form.addRow(botones)

        self._formato.currentTextChanged.connect(self._sincronizar)
        self._sincronizar()

    def formato(self) -> FormatoImagen:
        return _FORMATOS[self._formato.currentText()]

    def dpi(self) -> int:
        return int(self._dpi.value())

    def calidad(self) -> int:
        return int(self._calidad.value())

    # -- Interno ------------------------------------------------------------

    def _sincronizar(self) -> None:
        formato = self.formato()
        self._calidad.setEnabled(formato.admite_calidad)
        self._dpi.setEnabled(not formato.es_vectorial)
        if formato.es_vectorial:
            self._nota.setText(
                "El SVG conserva el texto y los trazos del original: no depende de "
                "la resolución. Un fichero por página."
            )
        elif formato.es_multipagina:
            self._nota.setText("Todas las páginas van dentro del mismo fichero .tiff.")
        else:
            self._nota.setText("Un fichero por página.")
