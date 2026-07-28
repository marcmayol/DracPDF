"""Puerto de conversión entrante Markdown / HTML / texto plano → PDF.

Opera sobre un fichero externo (no sobre el documento abierto). El adaptador que
lo implementa usa Qt y vive fuera del core.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.conversion import ConfigPagina
from lectorpdf.core.domain.herramientas import Progreso


@runtime_checkable
class ConversorTexto(Protocol):
    def a_pdf(
        self,
        ruta: Path,
        destino: Path,
        config: ConfigPagina,
        progreso: Progreso | None = None,
    ) -> None: ...
