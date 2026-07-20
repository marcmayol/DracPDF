"""Puerto de búsqueda de texto en el documento abierto.

Operación de solo lectura sobre el documento abierto (por `documento_id`). Al
recorrer todas las páginas puede ser larga, así que acepta el callback de
progreso del dominio (para ejecutarla en un hilo y poder cancelarla).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.contenido import Coincidencia
from lectorpdf.core.domain.herramientas import Progreso


@runtime_checkable
class ServicioBusqueda(Protocol):
    def buscar(
        self,
        documento_id: str,
        termino: str,
        coincidir_mayusculas: bool = False,
        progreso: Progreso | None = None,
    ) -> tuple[Coincidencia, ...]: ...
