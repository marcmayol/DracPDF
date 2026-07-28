"""Entidades de dominio para convertir las tablas de un PDF a hoja de cálculo.

Un PDF no sabe qué es una tabla: hay que deducirla. Por eso la detección se
declara con su estrategia y se enseña el resultado ANTES de escribir ficheros.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EstrategiaTablas(Enum):
    """Cómo se buscan las tablas en la página.

    `LINEAS` se fía de las líneas dibujadas: lo que encuentra suele ser una tabla
    de verdad, pero no ve las que solo están alineadas con espacios. `TEXTO`
    deduce las columnas de la posición del texto: encuentra esas, y también
    troceará en celdas párrafos que no son tablas.
    """

    LINEAS = "lines"
    TEXTO = "text"

    @property
    def es_aproximada(self) -> bool:
        return self is EstrategiaTablas.TEXTO


class FormatoTabla(Enum):
    CSV = "csv"  # un fichero por tabla
    XLSX = "xlsx"  # un solo libro, una hoja por tabla

    @property
    def extension(self) -> str:
        return f".{self.value}"


@dataclass(frozen=True)
class TablaDetectada:
    """Lo que se sabe de una tabla antes de convertirla."""

    pagina: int  # índice 0-based
    indice: int  # nº de tabla dentro de la página, 0-based
    filas: int
    columnas: int

    @property
    def nombre(self) -> str:
        """Identificador estable para el fichero o la hoja de destino."""
        return f"p{self.pagina + 1}_t{self.indice + 1}"
