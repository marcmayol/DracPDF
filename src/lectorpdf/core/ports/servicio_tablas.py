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

    def exportar_texto_como_hoja(
        self,
        documento_id: str,
        destino: Path,
        formato: FormatoTabla,
        progreso: Progreso | None = None,
    ) -> Path | None:
        """Vuelca todo el texto del documento a un único fichero.

        Sin detectar tablas: cada línea es una fila. Devuelve `None` si el
        documento no tiene ni una palabra (un escaneado, por ejemplo), para que
        el caso de uso lo diga en vez de dejar un fichero vacío."""
        ...
