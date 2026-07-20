"""Puerto de las propiedades del documento abierto (metadatos y datos técnicos)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.contenido import PropiedadesDocumento


@runtime_checkable
class ServicioPropiedades(Protocol):
    def propiedades(self, documento_id: str) -> PropiedadesDocumento: ...
