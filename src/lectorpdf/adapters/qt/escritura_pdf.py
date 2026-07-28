"""Paginado y escritura de un `QTextDocument` a PDF.

Lo comparten los conversores entrantes que pasan por Qt (Word, Markdown, HTML,
texto plano, ODT y RTF): todos acaban componiendo un QTextDocument que hay que
paginar sobre el tamaño y los márgenes elegidos. Escritura atómica.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QMarginsF, QSizeF
from PySide6.QtGui import QPageLayout, QPageSize, QPdfWriter, QTextDocument

from lectorpdf.core.domain.conversion import ConfigPagina


def escribir_pdf(
    documento: QTextDocument, destino: Path, config: ConfigPagina
) -> None:
    tmp = destino.with_name(destino.name + ".tmp")
    escritor = QPdfWriter(str(tmp))
    escritor.setPageSize(
        QPageSize(QSizeF(config.ancho_mm, config.alto_mm), QPageSize.Unit.Millimeter)
    )
    margen = QMarginsF(
        config.margen_mm, config.margen_mm, config.margen_mm, config.margen_mm
    )
    escritor.setPageMargins(margen, QPageLayout.Unit.Millimeter)

    # El QTextDocument pagina sobre el área imprimible del escritor.
    documento.print_(escritor)
    del escritor  # cierra el fichero antes del replace (Windows)
    os.replace(tmp, destino)
