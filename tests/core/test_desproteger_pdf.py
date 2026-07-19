"""Tests del caso de uso DesprotegerPdf con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.errores import DocumentoNoEncontrado
from lectorpdf.core.use_cases.desproteger_pdf import DesprotegerPdf
from tests.core.fakes import FakeServicioHerramientas


def test_desproteger_delega(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()
    ruta = tmp_path / "prot.pdf"
    ruta.write_bytes(b"%PDF-1.7\n")
    destino = tmp_path / "desp.pdf"

    DesprotegerPdf(servicio).ejecutar(ruta, "clave", destino)

    assert servicio.desprotecciones == [(ruta, "clave", destino)]


def test_fichero_inexistente(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()

    with pytest.raises(DocumentoNoEncontrado):
        DesprotegerPdf(servicio).ejecutar(tmp_path / "no.pdf", "x", tmp_path / "o.pdf")
    assert servicio.desprotecciones == []
