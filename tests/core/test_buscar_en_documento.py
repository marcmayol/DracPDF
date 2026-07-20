"""Tests del caso de uso BuscarEnDocumento con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.contenido import Coincidencia
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.buscar_en_documento import BuscarEnDocumento
from tests.core.fakes import FakeServicioBusqueda


def _documento() -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("d.pdf"),
        paginas=(Pagina(0, 400.0, 600.0),),
    )


def _coincidencia() -> Coincidencia:
    return Coincidencia(0, RectanguloPt(1.0, 2.0, 3.0, 4.0))


def test_delega_con_el_id_y_los_parametros() -> None:
    servicio = FakeServicioBusqueda((_coincidencia(),))

    resultado = BuscarEnDocumento(servicio).ejecutar(
        _documento(), "Ladon", coincidir_mayusculas=True
    )

    assert servicio.llamadas == [("doc-1", "Ladon", True)]
    assert resultado == (_coincidencia(),)


def test_termino_vacio_no_busca() -> None:
    servicio = FakeServicioBusqueda((_coincidencia(),))

    assert BuscarEnDocumento(servicio).ejecutar(_documento(), "") == ()
    assert servicio.llamadas == []


def test_reenvia_el_progreso() -> None:
    servicio = FakeServicioBusqueda()
    hechos: list[tuple[int, int]] = []

    BuscarEnDocumento(servicio).ejecutar(
        _documento(), "x", progreso=lambda h, t: hechos.append((h, t))
    )

    assert hechos == [(1, 1)]
