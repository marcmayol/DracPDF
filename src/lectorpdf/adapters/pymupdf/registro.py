"""Registro compartido de documentos PyMuPDF abiertos.

Es dueño de todo el estado por documento: el `fitz.Document`, su ciclo de vida y
sus *marcas* de estado (p. ej. si tiene cambios sin guardar). Todos los
adaptadores PyMuPDF (render, formularios, estampado y, más adelante, firma)
reciben este registro y solo hacen `obtener(id)` y marcan/consultan estado;
nunca cierran documentos ni conocen a los demás adaptadores.
"""

from __future__ import annotations

import uuid
from enum import Enum, auto

import fitz

from lectorpdf.core.domain.errores import DocumentoNoAbierto


class Marca(Enum):
    """Estados por documento. Ampliable en fases futuras (p. ej. FIRMADO)."""

    CAMBIOS_SIN_GUARDAR = auto()


class RegistroDocumentos:
    def __init__(self) -> None:
        self._documentos: dict[str, fitz.Document] = {}
        self._marcas: dict[str, set[Marca]] = {}

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
        """Cierra y elimina el documento y sus marcas. Idempotente."""
        documento = self._documentos.pop(documento_id, None)
        self._marcas.pop(documento_id, None)  # sin marcas huérfanas
        if documento is not None:
            documento.close()

    # -- Marcas de estado por documento -------------------------------------

    def marcar(self, documento_id: str, marca: Marca) -> None:
        self._marcas.setdefault(documento_id, set()).add(marca)

    def desmarcar(self, documento_id: str, marca: Marca) -> None:
        marcas = self._marcas.get(documento_id)
        if marcas is not None:
            marcas.discard(marca)

    def tiene(self, documento_id: str, marca: Marca) -> bool:
        return marca in self._marcas.get(documento_id, set())

    def __contains__(self, documento_id: object) -> bool:
        return documento_id in self._documentos
