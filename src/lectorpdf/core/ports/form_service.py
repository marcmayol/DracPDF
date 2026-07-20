"""Puerto de acceso a los formularios AcroForm de un documento.

Comparte el `documento_id` de sesión con `DocumentRepository`: ambos operan
sobre el mismo documento a través del registro compartido del adaptador.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.formularios import CampoFormulario


@runtime_checkable
class FormService(Protocol):
    def es_xfa(self, documento_id: str) -> bool:
        """True si el documento usa formularios XFA (no soportados)."""
        ...

    def listar_campos(self, documento_id: str) -> tuple[CampoFormulario, ...]:
        """Devuelve los campos AcroForm del documento (texto/casilla/radio/combo/lista)."""
        ...

    def escribir_valor(self, documento_id: str, campo_id: str, valor: str) -> None:
        """Escribe `valor` en el campo y regenera su apariencia en el documento.

        Lanza `CampoNoEncontrado` si el id no existe.
        """
        ...

    def esta_sucio(self, documento_id: str) -> bool:
        """True si hay cambios en memoria sin guardar a disco."""
        ...

    def esta_firmado(self, documento_id: str) -> bool:
        """True si el documento contiene firmas (edición bloqueada)."""
        ...

    def guardar_incremental(self, documento_id: str, destino: Path | None) -> None:
        """Guarda los cambios. Con `destino=None` guarda incremental sobre el
        propio fichero; con un `destino` distinto hace un guardado completo.
        """
        ...
