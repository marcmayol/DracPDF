"""Registro compartido de documentos PyMuPDF abiertos.

Es dueño de todo el estado por documento: el `fitz.Document`, su ciclo de vida,
sus operaciones a nivel de fichero (guardar incremental, leer bytes de disco,
recargar) y sus *marcas* de estado (cambios sin guardar, firmado). Todos los
adaptadores reciben este registro y operan por id; nunca cierran documentos ni
conocen a los demás. El adaptador de firma (pyHanko) solo usa la interfaz de
rutas/bytes/ids de aquí, nunca fitz.
"""

from __future__ import annotations

import uuid
from enum import Enum, auto
from pathlib import Path

import fitz

from lectorpdf.core.domain.errores import DocumentoNoAbierto


class Marca(Enum):
    """Estados por documento. Ampliable en fases futuras."""

    CAMBIOS_SIN_GUARDAR = auto()
    FIRMADO = auto()  # tiene firma(s) digital(es): edición bloqueada


class RegistroDocumentos:
    def __init__(self) -> None:
        self._documentos: dict[str, fitz.Document] = {}
        self._marcas: dict[str, set[Marca]] = {}

    def registrar(self, documento: fitz.Document) -> str:
        """Registra un documento ya abierto y devuelve su id de sesión.

        Si el documento ya contiene firmas, queda marcado como FIRMADO (un PDF
        firmado por terceros se abre bloqueado).
        """
        documento_id = uuid.uuid4().hex
        self._documentos[documento_id] = documento
        if _esta_firmado(documento):
            self.marcar(documento_id, Marca.FIRMADO)
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
        self._marcas.pop(documento_id, None)
        if documento is not None:
            documento.close()

    # -- Operaciones a nivel de fichero -------------------------------------

    def ruta(self, documento_id: str) -> Path:
        return Path(self.obtener(documento_id).name)

    def bytes_en_disco(self, documento_id: str) -> bytes:
        """Bytes reales del fichero en disco (para verificar firmas: no se puede
        reescribir con fitz sin romper los rangos firmados)."""
        return self.ruta(documento_id).read_bytes()

    def guardar_incremental(self, documento_id: str, destino: Path | None) -> None:
        """Guarda el documento. Con `destino=None`, incremental sobre el propio
        fichero (preserva revisiones previas, incluidas firmas); con un `destino`
        distinto, guardado completo."""
        doc = self.obtener(documento_id)
        if destino is None:
            doc.save(doc.name, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        else:
            doc.save(str(destino))
        self.desmarcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)

    def recargar(self, documento_id: str) -> None:
        """Cierra el fitz actual y reabre el fichero de disco bajo el mismo id,
        recomputando la marca FIRMADO. Operación única para que ningún flujo deje
        el registro a medio recargar."""
        doc = self.obtener(documento_id)
        ruta = Path(doc.name)
        doc.close()
        nuevo = fitz.open(ruta)
        self._documentos[documento_id] = nuevo
        self.desmarcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)
        if _esta_firmado(nuevo):
            self.marcar(documento_id, Marca.FIRMADO)
        else:
            self.desmarcar(documento_id, Marca.FIRMADO)

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


def _esta_firmado(documento: fitz.Document) -> bool:
    """True si el documento contiene campos de firma (SigFlags presente)."""
    return bool(documento.get_sigflags() > 0)
