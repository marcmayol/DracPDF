"""Tests del caso de uso ComprimirPdf con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.herramientas import ResultadoCompresion
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.comprimir_pdf import ComprimirPdf
from tests.core.fakes import FakeServicioHerramientas


def _documento() -> Documento:
    return Documento(id="doc-1", ruta=Path("d.pdf"), paginas=(Pagina(0, 400.0, 600.0),))


def test_comprimir_delega_y_devuelve_resultado(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()
    servicio.resultado_compresion = ResultadoCompresion(1000, 400)
    destino = tmp_path / "c.pdf"

    resultado = ComprimirPdf(servicio).ejecutar(_documento(), destino)

    assert servicio.compresiones == [("doc-1", destino)]
    assert resultado.porcentaje_reduccion == 60.0
