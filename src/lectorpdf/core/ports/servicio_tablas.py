"""Puerto de detección y conversión de las tablas del documento abierto.

Detectar y convertir son operaciones separadas a propósito: la UI enseña lo que
se ha encontrado antes de escribir ningún fichero.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.herramientas import Progreso
from lectorpdf.core.domain.tablas import (
    EstrategiaTablas,
    FormatoTabla,
    TablaDetectada,
)


@runtime_checkable
class ServicioTablas(Protocol):
    def detectar_tablas(
        self,
        documento_id: str,
        estrategia: EstrategiaTablas = EstrategiaTablas.LINEAS,
        progreso: Progreso | None = None,
    ) -> tuple[TablaDetectada, ...]: ...

    def exportar_tablas(
        self,
        documento_id: str,
        directorio: Path,
        formato: FormatoTabla,
        estrategia: EstrategiaTablas = EstrategiaTablas.LINEAS,
        progreso: Progreso | None = None,
    ) -> list[Path]: ...
