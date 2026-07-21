"""Conversión PDF → Word (.docx) con pdf2docx, aislada en un solo módulo.

Único punto del proyecto que importa pdf2docx. Escritura atómica (temporal +
replace). El rango es 1-based inclusivo (dominio); pdf2docx usa start 0-based y
end exclusivo.
"""

from __future__ import annotations

import os
from pathlib import Path

from pdf2docx import Converter

from lectorpdf.core.domain.herramientas import Progreso, Rango


def convertir(
    ruta_pdf: Path,
    destino: Path,
    rango: Rango | None = None,
    progreso: Progreso | None = None,
) -> None:
    tmp = destino.with_name(destino.name + ".tmp")
    conversor = Converter(str(ruta_pdf))
    try:
        if rango is not None:
            conversor.convert(str(tmp), start=rango.inicio - 1, end=rango.fin)
        else:
            conversor.convert(str(tmp))
    finally:
        conversor.close()
    os.replace(tmp, destino)
    if progreso is not None:
        progreso(1, 1)  # conversión en un paso: no cancelable a mitad
