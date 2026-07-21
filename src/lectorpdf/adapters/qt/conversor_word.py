"""Adaptador de `ConversorWord` con Qt (Word → PDF "reformateado").

Cadena: mammoth convierte el .docx a HTML (con imágenes embebidas), QTextDocument
compone y pagina, y QPdfWriter escribe el PDF. Texto real seleccionable, tablas,
listas, negritas/cursivas e imágenes; conserva contenido y estructura, no el
diseño exacto del original. Escritura atómica (temporal + replace).

Vive fuera del core: el caso de uso solo conoce el puerto.
"""

from __future__ import annotations

import os
from pathlib import Path

import mammoth
from PySide6.QtCore import QMarginsF, QSizeF
from PySide6.QtGui import QPageLayout, QPageSize, QPdfWriter, QTextDocument

from lectorpdf.core.domain.conversion import ConfigPagina
from lectorpdf.core.domain.herramientas import Progreso


class ConversorWordQt:
    def a_pdf(
        self,
        ruta_docx: Path,
        destino: Path,
        config: ConfigPagina,
        progreso: Progreso | None = None,
    ) -> None:
        with open(ruta_docx, "rb") as fichero:
            html = mammoth.convert_to_html(fichero).value  # imágenes embebidas

        documento = QTextDocument()
        documento.setHtml(html)

        tmp = destino.with_name(destino.name + ".tmp")
        escritor = QPdfWriter(str(tmp))
        escritor.setPageSize(
            QPageSize(
                QSizeF(config.ancho_mm, config.alto_mm), QPageSize.Unit.Millimeter
            )
        )
        margen = QMarginsF(
            config.margen_mm, config.margen_mm, config.margen_mm, config.margen_mm
        )
        escritor.setPageMargins(margen, QPageLayout.Unit.Millimeter)

        # El QTextDocument pagina sobre el área imprimible del escritor.
        documento.print_(escritor)
        del escritor  # cierra el fichero antes del replace (Windows)
        os.replace(tmp, destino)
        if progreso is not None:
            progreso(1, 1)  # conversión en un paso
