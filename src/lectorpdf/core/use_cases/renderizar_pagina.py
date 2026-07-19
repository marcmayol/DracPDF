"""Caso de uso: renderizar una página a una escala dada.

Es el punto de entrada único al renderizado. No guarda estado: recibe la escala
como dato y devuelve la imagen. La UI traduce su zoom a escala y cachea el
resultado por su cuenta.
"""

from __future__ import annotations

from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada
from lectorpdf.core.ports.document_repository import DocumentRepository


class RenderizarPagina:
    def __init__(self, repositorio: DocumentRepository) -> None:
        self._repositorio = repositorio

    def ejecutar(
        self, documento: Documento, indice: int, escala: float
    ) -> ImagenRenderizada:
        if indice < 0 or indice >= documento.num_paginas:
            raise PaginaFueraDeRango(
                f"Página {indice} fuera de rango [0, {documento.num_paginas})"
            )
        if escala <= 0:
            raise ValueError(f"La escala debe ser positiva, recibido: {escala}")
        return self._repositorio.renderizar_pagina(documento.id, indice, escala)
