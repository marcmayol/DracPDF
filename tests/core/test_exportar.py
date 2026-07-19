"""Tests de los casos de uso de exportación con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.exportar_imagenes import ExportarImagenes
from lectorpdf.core.use_cases.exportar_texto import ExportarTexto
from tests.core.fakes import FakeServicioHerramientas


def _documento() -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("d.pdf"),
        paginas=(Pagina(0, 400.0, 600.0), Pagina(1, 400.0, 600.0)),
    )


def test_exportar_png_delega_con_dpi(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()

    ExportarImagenes(servicio).ejecutar(_documento(), tmp_path, dpi=200)

    assert servicio.exportaciones_png == [("doc-1", tmp_path, 200)]


def test_exportar_png_dpi_invalido(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()

    with pytest.raises(ValueError):
        ExportarImagenes(servicio).ejecutar(_documento(), tmp_path, dpi=0)
    assert servicio.exportaciones_png == []


def test_exportar_texto_delega(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()
    destino = tmp_path / "t.txt"

    ExportarTexto(servicio).ejecutar(_documento(), destino)

    assert servicio.exportaciones_texto == [("doc-1", destino)]
