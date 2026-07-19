"""Caso de uso: abrir un documento PDF."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.errores import DocumentoNoEncontrado, FormatoNoSoportado
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.document_repository import DocumentRepository


class AbrirDocumento:
    """Valida la ruta y delega la apertura en el repositorio."""

    def __init__(self, repositorio: DocumentRepository) -> None:
        self._repositorio = repositorio

    def ejecutar(self, ruta: Path) -> Documento:
        if not ruta.exists() or not ruta.is_file():
            raise DocumentoNoEncontrado(f"No existe el fichero: {ruta}")
        if ruta.suffix.lower() != ".pdf":
            raise FormatoNoSoportado(f"No es un PDF: {ruta.name}")
        return self._repositorio.abrir(ruta)
