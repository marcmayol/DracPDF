"""Tests del caso de uso ProtegerPdf con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.proteger_pdf import ProtegerPdf
from tests.core.fakes import FakeServicioHerramientas


def _documento() -> Documento:
    return Documento(id="doc-1", ruta=Path("d.pdf"), paginas=(Pagina(0, 400.0, 600.0),))


def test_proteger_delega(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()
    destino = tmp_path / "p.pdf"

    ProtegerPdf(servicio).ejecutar(_documento(), destino, "clave")

    assert servicio.protecciones == [("doc-1", destino, "clave")]


def test_contrasena_vacia_es_error(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()

    with pytest.raises(ValueError):
        ProtegerPdf(servicio).ejecutar(_documento(), tmp_path / "p.pdf", "")
    assert servicio.protecciones == []
