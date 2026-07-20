"""Puerto de los enlaces de una página del documento abierto. Solo lectura."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.contenido import Enlace


@runtime_checkable
class ServicioEnlaces(Protocol):
    def enlaces(self, documento_id: str, pagina: int) -> tuple[Enlace, ...]: ...
