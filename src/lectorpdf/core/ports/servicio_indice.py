"""Puerto del índice (outline/marcadores) del documento abierto. Solo lectura."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.contenido import EntradaIndice


@runtime_checkable
class ServicioIndice(Protocol):
    def indice(self, documento_id: str) -> tuple[EntradaIndice, ...]: ...
