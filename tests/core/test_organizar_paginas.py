"""Tests del caso de uso OrganizarPaginas con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.organizar_paginas import OrganizarPaginas
from tests.core.fakes import FakeServicioHerramientas


def _documento(n: int = 3) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(Pagina(i, 400.0, 600.0) for i in range(n)),
    )


def test_rotar_delega_y_devuelve_documento_actualizado() -> None:
    servicio = FakeServicioHerramientas()
    servicio.paginas_resultado = (Pagina(0, 400.0, 600.0),)

    nuevo = OrganizarPaginas(servicio).rotar(_documento(), indice=1, grados=90)

    assert servicio.rotaciones == [("doc-1", 1, 90)]
    assert nuevo.paginas == servicio.paginas_resultado
    assert nuevo.id == "doc-1"


def test_eliminar_delega() -> None:
    servicio = FakeServicioHerramientas()
    servicio.paginas_resultado = (Pagina(0, 400.0, 600.0), Pagina(1, 400.0, 600.0))

    nuevo = OrganizarPaginas(servicio).eliminar(_documento(), indice=2)

    assert servicio.eliminaciones == [("doc-1", 2)]
    assert nuevo.num_paginas == 2


def test_mover_delega() -> None:
    servicio = FakeServicioHerramientas()
    servicio.paginas_resultado = tuple(Pagina(i, 400.0, 600.0) for i in range(3))

    OrganizarPaginas(servicio).mover(_documento(), origen=0, destino=2)

    assert servicio.movimientos == [("doc-1", 0, 2)]
