"""Puerto de conversión entrante imágenes → PDF.

Opera sobre ficheros externos (no sobre el documento abierto): no usa el
registro. El adaptador que lo implementa vive fuera del core.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.conversion import AjusteImagen, ConfigPagina
from lectorpdf.core.domain.herramientas import Progreso


@runtime_checkable
class ConversorImagenes(Protocol):
    def a_pdf(
        self,
        rutas: Sequence[Path],
        destino: Path,
        ajuste: AjusteImagen,
        config: ConfigPagina,
        progreso: Progreso | None = None,
    ) -> None: ...
