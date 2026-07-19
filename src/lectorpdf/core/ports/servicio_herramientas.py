"""Puerto de las herramientas de PDF (unir, organizar, dividir, proteger…).

Operaciones síncronas. Las que trabajan sobre el documento abierto reciben su
`documento_id`; unir y desproteger trabajan sobre rutas de ficheros cerrados.
Las operaciones largas aceptan un callback de progreso del dominio.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.herramientas import Progreso, Rango, ResultadoCompresion
from lectorpdf.core.domain.modelos import Pagina


@runtime_checkable
class ServicioHerramientas(Protocol):
    # -- Sobre rutas de ficheros cerrados -----------------------------------

    def unir(
        self, rutas: Sequence[Path], destino: Path, progreso: Progreso | None = None
    ) -> None: ...

    def desproteger(self, ruta: Path, contrasena: str, destino: Path) -> None: ...

    # -- Sobre el documento abierto (mutan: rechazan si FIRMADO) -------------

    def rotar_pagina(
        self, documento_id: str, indice: int, grados: int
    ) -> tuple[Pagina, ...]: ...

    def eliminar_pagina(
        self, documento_id: str, indice: int
    ) -> tuple[Pagina, ...]: ...

    def mover_pagina(
        self, documento_id: str, origen: int, destino: int
    ) -> tuple[Pagina, ...]: ...

    # -- Sobre el documento abierto (derivan a fichero nuevo) ---------------

    def dividir(
        self, documento_id: str, rangos: Sequence[Rango], directorio: Path
    ) -> list[Path]: ...

    def proteger(self, documento_id: str, destino: Path, contrasena: str) -> None: ...

    def comprimir(
        self, documento_id: str, destino: Path, progreso: Progreso | None = None
    ) -> ResultadoCompresion: ...

    def exportar_png(
        self,
        documento_id: str,
        directorio: Path,
        dpi: int,
        progreso: Progreso | None = None,
    ) -> list[Path]: ...

    def exportar_texto(self, documento_id: str, destino: Path) -> None: ...
