"""Tests del volcado del texto de un PDF a filas de hoja de cálculo.

La lógica vive en el dominio y se prueba sin PyMuPDF: se le dan palabras con su
sitio en la página y se comprueba dónde parte las celdas.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.contenido import PalabraTexto
from lectorpdf.core.domain.errores import ErrorDominio
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.domain.tablas import (
    HUECO_COLUMNA_PT,
    FormatoTabla,
    filas_desde_palabras,
)
from lectorpdf.core.use_cases.convertir_texto_a_hoja import ConvertirTextoAHoja


def _palabra(texto: str, x0: float, linea: int = 0, bloque: int = 0) -> PalabraTexto:
    """Una palabra en (x0, y) con un ancho proporcional a sus letras."""
    y = 100.0 + linea * 14.0
    return PalabraTexto(
        RectanguloPt(x0, y, x0 + len(texto) * 5.0, y + 10.0), texto, bloque, linea
    )


def test_las_palabras_seguidas_van_en_la_misma_celda() -> None:
    palabras = [_palabra("Total", 50.0), _palabra("anual", 78.0)]

    assert filas_desde_palabras(palabras) == [["Total anual"]]


def test_un_hueco_ancho_abre_una_columna_nueva() -> None:
    # "Enero" acaba en 75 y "120" empieza en 200: el vacío es una columna.
    palabras = [_palabra("Enero", 50.0), _palabra("120", 200.0)]

    assert filas_desde_palabras(palabras) == [["Enero", "120"]]


def test_cada_linea_es_una_fila_y_conserva_el_orden() -> None:
    palabras = [
        _palabra("Mes", 50.0, linea=0),
        _palabra("Gasto", 200.0, linea=0),
        _palabra("Enero", 50.0, linea=1),
        _palabra("120", 200.0, linea=1),
    ]

    assert filas_desde_palabras(palabras) == [["Mes", "Gasto"], ["Enero", "120"]]


def test_lo_que_esta_a_la_misma_altura_es_la_misma_fila() -> None:
    # Las celdas de una tabla suelen venir en bloques distintos aunque se lean
    # seguidas: manda la altura, no lo que declare el PDF.
    palabras = [
        _palabra("Enero", 50.0, linea=0, bloque=0),
        _palabra("120", 200.0, linea=0, bloque=7),
    ]

    assert filas_desde_palabras(palabras) == [["Enero", "120"]]


def test_las_alturas_distintas_siguen_siendo_filas_distintas() -> None:
    palabras = [
        _palabra("Uno", 50.0, linea=0, bloque=0),
        _palabra("Dos", 50.0, linea=1, bloque=0),
    ]

    assert filas_desde_palabras(palabras) == [["Uno"], ["Dos"]]


def test_las_palabras_desordenadas_se_colocan_por_su_posicion() -> None:
    palabras = [_palabra("120", 200.0), _palabra("Enero", 50.0)]

    assert filas_desde_palabras(palabras) == [["Enero", "120"]]


def test_el_umbral_del_hueco_es_ajustable() -> None:
    palabras = [_palabra("a", 50.0), _palabra("b", 62.0)]  # hueco de 7 pt

    assert filas_desde_palabras(palabras, hueco_min_pt=20.0) == [["a b"]]
    assert filas_desde_palabras(palabras, hueco_min_pt=5.0) == [["a", "b"]]


def test_el_umbral_por_defecto_es_mayor_que_un_espacio_normal() -> None:
    # Si fuese del tamaño de un espacio, cada palabra sería una columna.
    assert HUECO_COLUMNA_PT > 3.0


def test_una_pagina_sin_palabras_no_da_filas() -> None:
    assert filas_desde_palabras([]) == []


class FakeServicioHoja:
    """Fake del puerto: apunta lo que le piden y devuelve lo que se le diga."""

    def __init__(self, destino: Path | None) -> None:
        self._destino = destino
        self.peticiones: list[tuple[str, Path, FormatoTabla]] = []

    def exportar_texto_como_hoja(  # type: ignore[no-untyped-def]
        self, documento_id, destino, formato, progreso=None
    ):
        self.peticiones.append((documento_id, destino, formato))
        return self._destino


def _documento() -> Documento:
    return Documento(id="doc-1", ruta=Path("d.pdf"), paginas=(Pagina(0, 400.0, 600.0),))


def test_convertir_devuelve_el_fichero_escrito(tmp_path: Path) -> None:
    destino = tmp_path / "d.xlsx"
    servicio = FakeServicioHoja(destino)

    escrito = ConvertirTextoAHoja(servicio).ejecutar(
        _documento(), destino, FormatoTabla.XLSX
    )

    assert escrito == destino
    assert servicio.peticiones == [("doc-1", destino, FormatoTabla.XLSX)]


def test_un_pdf_sin_texto_avisa_en_vez_de_dejar_un_fichero_vacio(
    tmp_path: Path,
) -> None:
    # Un PDF escaneado son imágenes: no hay ni una palabra que volcar.
    servicio = FakeServicioHoja(None)

    with pytest.raises(ErrorDominio, match="texto"):
        ConvertirTextoAHoja(servicio).ejecutar(
            _documento(), tmp_path / "d.csv", FormatoTabla.CSV
        )
