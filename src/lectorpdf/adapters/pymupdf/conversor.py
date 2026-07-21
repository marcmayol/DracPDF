"""Adaptador de `ConversorPDF` sobre PyMuPDF (conversiones salientes).

Lee el documento abierto del registro compartido (estado actual en memoria, no el
de disco) y lo convierte. HTML y Markdown usan fitz directamente; Word delega en
el módulo aislado de pdf2docx. Las conversiones no mutan el original: se permiten
aunque esté firmado.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.herramientas import Progreso, Rango


class ConversorFitz:
    def __init__(self, registro: RegistroDocumentos) -> None:
        self._registro = registro

    def a_word(
        self,
        documento_id: str,
        destino: Path,
        rango: Rango | None = None,
        progreso: Progreso | None = None,
    ) -> None:
        # pdf2docx trabaja sobre un fichero; se vuelca el estado actual del
        # documento (incluye ediciones sin guardar) a un PDF temporal.
        from lectorpdf.adapters.pdf2docx.pdf_a_docx import convertir

        doc = self._registro.obtener(documento_id)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            temporal = Path(tf.name)
        try:
            doc.save(str(temporal))
            convertir(temporal, destino, rango, progreso)
        finally:
            temporal.unlink(missing_ok=True)
