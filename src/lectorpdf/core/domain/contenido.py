"""Entidades de dominio para el contenido del documento (Fase 8).

Búsqueda, selección, índice, enlaces y propiedades: lecturas del documento que
no lo modifican. Las coordenadas van en puntos PDF, con el mismo convenio que el
resto del dominio (origen arriba-izquierda), para poder mapearlas a la escena con
la misma traducción que usan los formularios.
"""

from __future__ import annotations

from dataclasses import dataclass

from lectorpdf.core.domain.formularios import RectanguloPt


@dataclass(frozen=True)
class Coincidencia:
    """Una ocurrencia del término buscado: página (0-based) y su rect en puntos."""

    pagina: int
    rect_pt: RectanguloPt


@dataclass(frozen=True)
class PalabraTexto:
    """Una palabra de una página con su rect (puntos) y su posición de lectura.

    `bloque` y `linea` permiten reconstruir los saltos de línea/párrafo al copiar
    y delimitar la selección por palabra (doble clic) o párrafo (triple clic)."""

    rect_pt: RectanguloPt
    texto: str
    bloque: int
    linea: int
