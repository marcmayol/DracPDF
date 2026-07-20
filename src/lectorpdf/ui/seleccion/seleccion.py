"""Lógica pura de selección de texto sobre una página (sin Qt).

Trabaja sobre las palabras en orden de lectura (`PalabraTexto`): decide qué
palabra hay bajo un punto, delimita la palabra/párrafo (doble/triple clic), el
rango arrastrado entre dos palabras y reconstruye el texto con sus saltos.
Aislada de Qt para poder testearla directamente.
"""

from __future__ import annotations

from collections.abc import Sequence

from lectorpdf.core.domain.contenido import PalabraTexto


def indice_en_punto(
    palabras: Sequence[PalabraTexto], x: float, y: float
) -> int | None:
    """Índice de la palabra cuyo rectángulo contiene el punto (en puntos PDF)."""
    for i, p in enumerate(palabras):
        r = p.rect_pt
        if r.x0 <= x <= r.x1 and r.y0 <= y <= r.y1:
            return i
    return None


def indice_mas_cercano(
    palabras: Sequence[PalabraTexto], x: float, y: float
) -> int | None:
    """Índice de la palabra más cercana al punto (para arrastrar entre palabras).

    Prioriza la línea vertical más próxima y, dentro de ella, la horizontal."""
    if not palabras:
        return None

    def distancia(p: PalabraTexto) -> tuple[float, float]:
        r = p.rect_pt
        cy = (r.y0 + r.y1) / 2.0
        dy = 0.0 if r.y0 <= y <= r.y1 else abs(cy - y)
        dx = 0.0 if r.x0 <= x <= r.x1 else min(abs(r.x0 - x), abs(r.x1 - x))
        return dy, dx

    return min(range(len(palabras)), key=lambda i: distancia(palabras[i]))


def rango(anclaje: int, cursor: int) -> tuple[int, int]:
    """Extremos ordenados (inicio, fin) del rango arrastrado, ambos inclusive."""
    return (anclaje, cursor) if anclaje <= cursor else (cursor, anclaje)


def indices_palabra(palabras: Sequence[PalabraTexto], indice: int) -> tuple[int, int]:
    """Rango de una sola palabra (doble clic)."""
    return indice, indice


def indices_parrafo(palabras: Sequence[PalabraTexto], indice: int) -> tuple[int, int]:
    """Rango del párrafo (bloque) que contiene la palabra (triple clic).

    Como las palabras vienen en orden de lectura, el bloque es contiguo."""
    if not palabras:
        return indice, indice
    bloque = palabras[indice].bloque
    inicio = indice
    while inicio > 0 and palabras[inicio - 1].bloque == bloque:
        inicio -= 1
    fin = indice
    while fin < len(palabras) - 1 and palabras[fin + 1].bloque == bloque:
        fin += 1
    return inicio, fin


def texto_de(palabras: Sequence[PalabraTexto], inicio: int, fin: int) -> str:
    """Texto del rango [inicio, fin] con espacios entre palabras y saltos de línea
    cuando cambia la línea o el bloque."""
    partes: list[str] = []
    for i in range(inicio, fin + 1):
        if i > inicio:
            previa = palabras[i - 1]
            actual = palabras[i]
            distinto = (
                actual.bloque != previa.bloque or actual.linea != previa.linea
            )
            partes.append("\n" if distinto else " ")
        partes.append(palabras[i].texto)
    return "".join(partes)
