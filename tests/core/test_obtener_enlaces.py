"""Test del caso de uso ObtenerEnlaces con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.contenido import Enlace
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.obtener_enlaces import ObtenerEnlaces


class _FakeEnlaces:
    def __init__(self, enlaces: tuple[Enlace, ...]) -> None:
        self._enlaces = enlaces
        self.llamadas: list[tuple[str, int]] = []

    def enlaces(self, documento_id: str, pagina: int) -> tuple[Enlace, ...]:
        self.llamadas.append((documento_id, pagina))
        return self._enlaces


def _documento() -> Documento:
    return Documento(id="doc-1", ruta=Path("d.pdf"), paginas=(Pagina(0, 400.0, 600.0),))


def test_delega_con_id_y_pagina() -> None:
    enlaces = (Enlace(RectanguloPt(0, 0, 1, 1), pagina_destino=2),)
    servicio = _FakeEnlaces(enlaces)

    resultado = ObtenerEnlaces(servicio).ejecutar(_documento(), 0)

    assert servicio.llamadas == [("doc-1", 0)]
    assert resultado == enlaces
