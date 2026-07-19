"""Tests del caso de uso UnirPdf con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.errores import DocumentoNoEncontrado
from lectorpdf.core.use_cases.unir_pdf import UnirPdf
from tests.core.fakes import FakeServicioHerramientas


def _ficheros(tmp_path: Path, n: int) -> list[Path]:
    rutas = []
    for i in range(n):
        r = tmp_path / f"f{i}.pdf"
        r.write_bytes(b"%PDF-1.7\n")
        rutas.append(r)
    return rutas


def test_unir_delegando_en_el_servicio(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()
    rutas = _ficheros(tmp_path, 3)
    destino = tmp_path / "unido.pdf"

    UnirPdf(servicio).ejecutar(rutas, destino)

    assert servicio.uniones == [(rutas, destino)]


def test_unir_requiere_al_menos_dos(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()

    with pytest.raises(ValueError):
        UnirPdf(servicio).ejecutar(_ficheros(tmp_path, 1), tmp_path / "u.pdf")
    assert servicio.uniones == []


def test_unir_fichero_inexistente(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()
    rutas = [*_ficheros(tmp_path, 2), tmp_path / "no_existe.pdf"]

    with pytest.raises(DocumentoNoEncontrado):
        UnirPdf(servicio).ejecutar(rutas, tmp_path / "u.pdf")
    assert servicio.uniones == []
