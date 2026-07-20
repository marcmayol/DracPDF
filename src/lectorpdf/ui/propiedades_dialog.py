"""Diálogo de propiedades del documento: metadatos y datos técnicos."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QWidget,
)

from lectorpdf.core.domain.contenido import PropiedadesDocumento


def formatear_tamano(n_bytes: int) -> str:
    """Tamaño legible: B, KB, MB o GB."""
    tamano = float(n_bytes)
    for unidad in ("B", "KB", "MB"):
        if tamano < 1024:
            return f"{tamano:.0f} {unidad}" if unidad == "B" else f"{tamano:.1f} {unidad}"
        tamano /= 1024
    return f"{tamano:.1f} GB"


class PropiedadesDialog(QDialog):
    def __init__(
        self,
        propiedades: PropiedadesDocumento,
        ruta: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Propiedades del documento")
        self.setMinimumWidth(420)

        form = QFormLayout(self)
        form.addRow("Fichero:", QLabel(ruta.name))
        form.addRow("Ruta:", QLabel(str(ruta)))
        form.addRow("Título:", QLabel(propiedades.titulo or "—"))
        form.addRow("Autor:", QLabel(propiedades.autor or "—"))
        form.addRow("Asunto:", QLabel(propiedades.asunto or "—"))
        form.addRow("Palabras clave:", QLabel(propiedades.palabras_clave or "—"))
        form.addRow("Creador:", QLabel(propiedades.creador or "—"))
        form.addRow("Productor:", QLabel(propiedades.productor or "—"))
        form.addRow("Versión PDF:", QLabel(propiedades.version_pdf or "—"))
        form.addRow("Cifrado:", QLabel("Sí" if propiedades.cifrado else "No"))
        form.addRow("Páginas:", QLabel(str(propiedades.num_paginas)))
        form.addRow("Tamaño:", QLabel(formatear_tamano(propiedades.tamano_bytes)))

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.rejected.connect(self.reject)
        botones.accepted.connect(self.accept)
        form.addRow(botones)
