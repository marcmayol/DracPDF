"""Entidades de dominio para convertir las tablas de un PDF a hoja de cálculo.

Un PDF no sabe qué es una tabla: hay que deducirla. Por eso la detección se
declara con su estrategia y se enseña el resultado ANTES de escribir ficheros.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from lectorpdf.core.domain.contenido import PalabraTexto

HUECO_COLUMNA_PT = 6.0
"""Vacío horizontal (en puntos) a partir del cual se abre una columna nueva.

Un espacio normal ronda los 2-3 pt en un cuerpo de 11 pt; quien alinea una
columna a mano deja bastante más. Con 6 pt, las palabras de una frase corriente
siguen juntas y las columnas separadas se parten."""


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


def filas_desde_palabras(
    palabras: Sequence[PalabraTexto], hueco_min_pt: float = HUECO_COLUMNA_PT
) -> list[list[str]]:
    """Vuelca las palabras de una página a filas de hoja de cálculo.

    Aquí no se detecta ninguna tabla: cada línea del documento es una fila, y
    dentro de la línea se abre una columna allí donde hay un vacío ancho. Es la
    conversión honesta de un texto que no dice cómo está organizado — lo que
    esté alineado en columnas caerá en columnas, y lo demás será una frase en
    una sola celda.
    """
    filas: list[list[str]] = []
    for linea in _agrupar_por_altura(palabras):
        celdas: list[str] = []
        fin_anterior: float | None = None
        for palabra in sorted(linea, key=lambda p: p.rect_pt.x0):
            texto = palabra.texto.strip()
            if not texto:
                continue
            if fin_anterior is None or palabra.rect_pt.x0 - fin_anterior >= hueco_min_pt:
                celdas.append(texto)
            else:
                celdas[-1] = f"{celdas[-1]} {texto}"
            fin_anterior = palabra.rect_pt.x1
        if celdas:
            filas.append(celdas)
    return filas


def _agrupar_por_altura(palabras: Sequence[PalabraTexto]) -> list[list[PalabraTexto]]:
    """Reúne en una misma fila las palabras que están a la misma altura.

    No sirve agruparlas por el bloque y la línea que declara el PDF: las celdas
    de una tabla suelen venir en bloques distintos aunque se lean en la misma
    fila, y entonces cada celda saldría en su propia fila. Lo que hace el ojo es
    mirar la altura, y eso es lo que se hace aquí: dos palabras van juntas si sus
    bandas verticales se solapan por más de la mitad de la más baja.
    """
    lineas: list[list[PalabraTexto]] = []
    bandas: list[tuple[float, float]] = []
    for palabra in sorted(palabras, key=lambda p: (p.rect_pt.y0, p.rect_pt.x0)):
        rect = palabra.rect_pt
        for indice, (arriba, abajo) in enumerate(bandas):
            solape = min(abajo, rect.y1) - max(arriba, rect.y0)
            menor_alto = min(abajo - arriba, rect.alto)
            if menor_alto > 0 and solape > menor_alto / 2:
                lineas[indice].append(palabra)
                bandas[indice] = (min(arriba, rect.y0), max(abajo, rect.y1))
                break
        else:
            lineas.append([palabra])
            bandas.append((rect.y0, rect.y1))
    return lineas
