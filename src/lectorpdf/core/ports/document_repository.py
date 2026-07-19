"""Puerto de acceso a documentos PDF. El core define la interfaz; el adaptador la implementa."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada


@runtime_checkable
class DocumentRepository(Protocol):
    """Abre documentos y renderiza sus páginas a mapas de bits RGBA.

    Las implementaciones mantienen el estado nativo (p. ej. el objeto de PyMuPDF)
    indexado por el `id` del documento; el core solo maneja ese identificador.
    """

    def abrir(self, ruta: Path) -> Documento:
        """Abre el PDF y devuelve sus metadatos.

        Lanza `DocumentoNoEncontrado` si la ruta no existe y `FormatoNoSoportado`
        si el fichero no es un PDF legible.
        """
        ...

    def renderizar_pagina(
        self, documento_id: str, indice: int, escala: float
    ) -> ImagenRenderizada:
        """Renderiza la página `indice` (0-based) a `escala` (1.0 = 72 DPI).

        Lanza `DocumentoNoAbierto` si el id no está abierto.
        """
        ...

    def cerrar(self, documento_id: str) -> None:
        """Libera el documento. Idempotente: cerrar un id desconocido no falla."""
        ...
