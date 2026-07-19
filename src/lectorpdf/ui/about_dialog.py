"""Diálogo "Acerca de" con el logo y el nombre de la aplicación."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from lectorpdf import __version__
from lectorpdf.ui.theme.marca import NOMBRE_APP, ruta_logo

_DESCRIPCION = "Visor de PDF con rellenado de formularios y firma digital."


class AboutDialog(QDialog):
    def __init__(self, es_oscuro: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Acerca de {NOMBRE_APP}")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        logo = ruta_logo(es_oscuro)
        if logo is not None:
            imagen = QLabel()
            imagen.setPixmap(
                QPixmap(str(logo)).scaledToHeight(
                    96, Qt.TransformationMode.SmoothTransformation
                )
            )
            imagen.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(imagen)

        titulo = QLabel(NOMBRE_APP)
        titulo.setStyleSheet("font-size: 20px; font-weight: 650;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(titulo)

        version = QLabel(f"versión {__version__}")
        version.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(version)

        descripcion = QLabel(_DESCRIPCION)
        descripcion.setWordWrap(True)
        descripcion.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(descripcion)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(self.reject)
        botones.accepted.connect(self.accept)
        layout.addWidget(botones)
