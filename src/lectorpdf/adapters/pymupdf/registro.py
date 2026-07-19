"""Registro compartido de documentos PyMuPDF abiertos.

Es dueño del ciclo de vida: mantiene el `fitz.Document` indexado por id de
sesión y es el único que llama a `doc.close()`. Todos los adaptadores PyMuPDF
(repositorio de render, servicio de formularios y, más adelante, firma) reciben
este registro y solo hacen `obtener(id)`; nunca cierran documentos ni conocen
a los demás adaptadores.
"""

from __future__ import annotations

import uuid

import fitz

from lectorpdf.core.domain.errores import DocumentoNoAbierto


class RegistroDocumentos:
    def __init__(self) -> None:
        self._documentos: dict[str, fitz.Document] = {}

    def registrar(self, documento: fitz.Document) -> str:
        """Registra un documento ya abierto y devuelve su id de sesión."""
        documento_id = uuid.uuid4().hex
        self._documentos[documento_id] = documento
        return documento_id

    def obtener(self, documento_id: str) -> fitz.Document:
        """Devuelve el documento o lanza `DocumentoNoAbierto` si no existe."""
        documento = self._documentos.get(documento_id)
        if documento is None:
            raise DocumentoNoAbierto(f"Documento no abierto: {documento_id}")
        return documento

    def cerrar(self, documento_id: str) -> None:
        """Cierra y elimina el documento. Idempotente."""
        documento = self._documentos.pop(documento_id, None)
        if documento is not None:
            documento.close()

    def __contains__(self, documento_id: object) -> bool:
        return documento_id in self._documentos
