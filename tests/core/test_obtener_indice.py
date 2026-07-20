"""Test del caso de uso ObtenerIndice con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.contenido import EntradaIndice
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.obtener_indice import ObtenerIndice


class _FakeIndice:
    def __init__(self, entradas: tuple[EntradaIndice, ...]) -> None:
        self._entradas = entradas
        self.llamadas: list[str] = []

    def indice(self, documento_id: str) -> tuple[EntradaIndice, ...]:
        self.llamadas.append(documento_id)
        return self._entradas


def _documento() -> Documento:
    return Documento(id="doc-1", ruta=Path("d.pdf"), paginas=(Pagina(0, 400.0, 600.0),))


def test_delega_con_el_id() -> None:
    entradas = (EntradaIndice(1, "Cap", 0),)
    servicio = _FakeIndice(entradas)

    resultado = ObtenerIndice(servicio).ejecutar(_documento())

    assert servicio.llamadas == ["doc-1"]
    assert resultado == entradas
