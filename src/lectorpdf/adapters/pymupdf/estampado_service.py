"""Adaptador de `EstampadoService` sobre PyMuPDF.

Comparte el `RegistroDocumentos` con los demás adaptadores. Al insertar la imagen
marca el documento con `CAMBIOS_SIN_GUARDAR` (mismo mecanismo que formularios;
PyMuPDF no fía is_dirty tras guardado incremental).
"""

from __future__ import annotations

import fitz

from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.errores import DocumentoFirmado, PaginaFueraDeRango
from lectorpdf.core.domain.formularios import RectanguloPt


class PyMuPDFEstampadoService:
    def __init__(self, registro: RegistroDocumentos) -> None:
        self._registro = registro

    def estampar_imagen(
        self,
        documento_id: str,
        pagina: int,
        rect_pt: RectanguloPt,
        imagen_png: bytes,
    ) -> None:
        if self._registro.tiene(documento_id, Marca.FIRMADO):
            raise DocumentoFirmado("El documento está firmado: no se puede estampar")
        doc = self._registro.obtener(documento_id)
        if pagina < 0 or pagina >= doc.page_count:
            raise PaginaFueraDeRango(
                f"Página {pagina} fuera de rango [0, {doc.page_count})"
            )
        rect = fitz.Rect(rect_pt.x0, rect_pt.y0, rect_pt.x1, rect_pt.y1)
        doc[pagina].insert_image(
            rect, stream=imagen_png, keep_proportion=True, overlay=True
        )
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)
