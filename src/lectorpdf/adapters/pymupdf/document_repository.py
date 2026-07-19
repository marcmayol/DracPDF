"""Adaptador de `DocumentRepository` sobre PyMuPDF (fitz).

Es la única capa que importa fitz. Mantiene los documentos nativos en un
registro indexado por el id de sesión y traduce los errores de PyMuPDF a
excepciones de dominio.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import fitz

from lectorpdf.core.domain.errores import (
    DocumentoNoAbierto,
    DocumentoNoEncontrado,
    FormatoNoSoportado,
    PaginaFueraDeRango,
)
from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina


class PyMuPDFDocumentRepository:
    """Implementa `DocumentRepository` con PyMuPDF."""

    def __init__(self) -> None:
        self._abiertos: dict[str, fitz.Document] = {}

    def abrir(self, ruta: Path) -> Documento:
        if not ruta.exists() or not ruta.is_file():
            raise DocumentoNoEncontrado(f"No existe el fichero: {ruta}")
        try:
            doc = fitz.open(ruta)
        except Exception as exc:  # PyMuPDF lanza fitz.FileDataError y otros
            raise FormatoNoSoportado(f"No se pudo abrir como PDF: {ruta.name}") from exc

        if not doc.is_pdf:
            doc.close()
            raise FormatoNoSoportado(f"El fichero no es un PDF: {ruta.name}")

        documento_id = uuid.uuid4().hex
        self._abiertos[documento_id] = doc

        paginas = tuple(
            Pagina(indice=i, ancho_pt=doc[i].rect.width, alto_pt=doc[i].rect.height)
            for i in range(doc.page_count)
        )
        titulo = (doc.metadata or {}).get("title") or None
        return Documento(id=documento_id, ruta=ruta, paginas=paginas, titulo=titulo)

    def renderizar_pagina(
        self, documento_id: str, indice: int, escala: float
    ) -> ImagenRenderizada:
        doc = self._abiertos.get(documento_id)
        if doc is None:
            raise DocumentoNoAbierto(f"Documento no abierto: {documento_id}")
        if indice < 0 or indice >= doc.page_count:
            raise PaginaFueraDeRango(
                f"Página {indice} fuera de rango [0, {doc.page_count})"
            )

        pagina = doc[indice]
        matriz = fitz.Matrix(escala, escala)
        pix = pagina.get_pixmap(matrix=matriz, alpha=True)
        return ImagenRenderizada(
            ancho_px=pix.width,
            alto_px=pix.height,
            datos=pix.samples,  # RGBA, ancho*alto*4 bytes
            escala=escala,
        )

    def cerrar(self, documento_id: str) -> None:
        doc = self._abiertos.pop(documento_id, None)
        if doc is not None:
            doc.close()
