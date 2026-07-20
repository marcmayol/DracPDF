"""Lógica pura de la lista de documentos recientes (sin Qt).

La ventana persiste la lista en QSettings; aquí solo se manipula la lista (añadir
al frente sin duplicados y con tope) y se elide una ruta larga para el menú.
"""

from __future__ import annotations

from collections.abc import Sequence

MAX_RECIENTES = 10


def anadir(actuales: Sequence[str], ruta: str, maximo: int = MAX_RECIENTES) -> list[str]:
    """Pone `ruta` al frente, sin duplicados, y recorta a `maximo` elementos."""
    lista = [r for r in actuales if r != ruta]
    lista.insert(0, ruta)
    return lista[:maximo]


def elidir(ruta: str, maximo: int = 50) -> str:
    """Acorta una ruta larga por el centro con '…' para mostrarla en el menú."""
    if len(ruta) <= maximo:
        return ruta
    if maximo <= 1:
        return "…"
    cabeza = (maximo - 1) // 2
    cola = maximo - 1 - cabeza
    return f"{ruta[:cabeza]}…{ruta[len(ruta) - cola:]}"
