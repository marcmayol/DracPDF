"""Puerto de conversión entrante Word → PDF.

Opera sobre un `.docx` externo (no sobre el documento abierto): no usa el
registro. El adaptador que lo implementa usa Qt (mammoth → HTML → QTextDocument →
QPdfWriter) y vive fuera del core; el caso de uso solo conoce este puerto.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.conversion import ConfigPagina
from lectorpdf.core.domain.herramientas import Progreso


@runtime_checkable
class ConversorWord(Protocol):
    def a_pdf(
        self,
        ruta_docx: Path,
        destino: Path,
        config: ConfigPagina,
        progreso: Progreso | None = None,
    ) -> None: ...
