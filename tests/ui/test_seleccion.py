"""Tests de la lógica pura de selección de texto (sin Qt)."""

from __future__ import annotations

from lectorpdf.core.domain.contenido import PalabraTexto
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.ui.seleccion import seleccion


def _palabra(texto: str, x0: float, bloque: int, linea: int) -> PalabraTexto:
    # Palabras de 20 pt de ancho y 10 de alto en la línea `linea` (y = linea*20).
    y0 = linea * 20.0
    return PalabraTexto(RectanguloPt(x0, y0, x0 + 20.0, y0 + 10.0), texto, bloque, linea)


def _parrafo() -> tuple[PalabraTexto, ...]:
    return (
        _palabra("Hola", 0.0, bloque=0, linea=0),
        _palabra("mundo", 25.0, bloque=0, linea=0),
        _palabra("otra", 0.0, bloque=0, linea=1),
        _palabra("linea", 25.0, bloque=0, linea=1),
        _palabra("Nuevo", 0.0, bloque=1, linea=2),
        _palabra("parrafo", 25.0, bloque=1, linea=2),
    )


def test_indice_en_punto_dentro_del_rect() -> None:
    palabras = _parrafo()
    assert seleccion.indice_en_punto(palabras, 30.0, 5.0) == 1  # "mundo"
    assert seleccion.indice_en_punto(palabras, 500.0, 500.0) is None


def test_indice_mas_cercano_prioriza_la_linea() -> None:
    palabras = _parrafo()
    # Punto a la derecha de la línea 1: la palabra más cercana es "linea" (idx 3).
    assert seleccion.indice_mas_cercano(palabras, 100.0, 25.0) == 3


def test_rango_ordena_los_extremos() -> None:
    assert seleccion.rango(3, 1) == (1, 3)
    assert seleccion.rango(2, 2) == (2, 2)


def test_indices_parrafo_abarca_el_bloque() -> None:
    palabras = _parrafo()
    assert seleccion.indices_parrafo(palabras, 0) == (0, 3)  # bloque 0
    assert seleccion.indices_parrafo(palabras, 5) == (4, 5)  # bloque 1


def test_texto_con_espacios_saltos_de_linea_y_parrafo() -> None:
    palabras = _parrafo()
    assert seleccion.texto_de(palabras, 0, 1) == "Hola mundo"
    assert seleccion.texto_de(palabras, 0, 3) == "Hola mundo\notra linea"
    assert seleccion.texto_de(palabras, 1, 4) == "mundo\notra linea\nNuevo"
