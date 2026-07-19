"""Caso de uso: dividir el documento abierto en varios ficheros."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from lectorpdf.core.domain.errores import RangoInvalido
from lectorpdf.core.domain.herramientas import Rango
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_herramientas import ServicioHerramientas


class DividirPdf:
    def __init__(self, servicio: ServicioHerramientas) -> None:
        self._servicio = servicio

    def por_paginas(self, documento: Documento, directorio: Path) -> list[Path]:
        rangos = [Rango(i + 1, i + 1) for i in range(documento.num_paginas)]
        return self._servicio.dividir(documento.id, rangos, directorio)

    def por_rangos(
        self, documento: Documento, rangos: Sequence[Rango], directorio: Path
    ) -> list[Path]:
        if not rangos:
            raise RangoInvalido("No se indicó ningún rango")
        for rango in rangos:
            if rango.inicio < 1 or rango.fin > documento.num_paginas:
                raise RangoInvalido(
                    f"Rango {rango.inicio}-{rango.fin} fuera de "
                    f"[1, {documento.num_paginas}]"
                )
        return self._servicio.dividir(documento.id, rangos, directorio)
