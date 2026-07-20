"""Test del caso de uso ObtenerPalabras con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.contenido import PalabraTexto
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.obtener_palabras import ObtenerPalabras


class _FakeTexto:
    def __init__(self) -> None:
        self.llamadas: list[tuple[str, int]] = []

    def palabras(self, documento_id: str, pagina: int) -> tuple[PalabraTexto, ...]:
        self.llamadas.append((documento_id, pagina))
        return (PalabraTexto(RectanguloPt(0, 0, 1, 1), "hola", 0, 0),)


def _documento() -> Documento:
    return Documento(id="doc-1", ruta=Path("d.pdf"), paginas=(Pagina(0, 400.0, 600.0),))


def test_delega_con_id_y_pagina() -> None:
    servicio = _FakeTexto()

    palabras = ObtenerPalabras(servicio).ejecutar(_documento(), 0)

    assert servicio.llamadas == [("doc-1", 0)]
    assert palabras[0].texto == "hola"
