"""Tests de integración de PyMuPDFHerramientas."""

from __future__ import annotations

from pathlib import Path

import fitz

from lectorpdf.adapters.pymupdf.herramientas import PyMuPDFHerramientas
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos


def _pdf(ruta: Path, textos: list[str]) -> Path:
    doc = fitz.open()
    for texto in textos:
        pagina = doc.new_page(width=300, height=400)
        pagina.insert_text((40, 60), texto, fontsize=14)
    doc.save(ruta)
    doc.close()
    return ruta


def _servicio() -> PyMuPDFHerramientas:
    return PyMuPDFHerramientas(RegistroDocumentos())


def test_unir_respeta_el_orden(tmp_path: Path) -> None:
    a = _pdf(tmp_path / "a.pdf", ["A1", "A2"])
    b = _pdf(tmp_path / "b.pdf", ["B1"])
    destino = tmp_path / "unido.pdf"

    _servicio().unir([b, a], destino)  # b antes que a

    doc = fitz.open(destino)
    assert doc.page_count == 3
    assert doc[0].get_text().strip() == "B1"
    assert doc[1].get_text().strip() == "A1"
    doc.close()


def test_unir_reporta_progreso(tmp_path: Path) -> None:
    rutas = [
        _pdf(tmp_path / "a.pdf", ["A"]),
        _pdf(tmp_path / "b.pdf", ["B"]),
        _pdf(tmp_path / "c.pdf", ["C"]),
    ]
    progresos: list[tuple[int, int]] = []

    _servicio().unir(rutas, tmp_path / "u.pdf", lambda h, t: progresos.append((h, t)))

    assert progresos[-1] == (3, 3)
