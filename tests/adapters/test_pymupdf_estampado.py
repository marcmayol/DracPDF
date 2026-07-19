"""Tests del adaptador de estampado PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.estampado_service import PyMuPDFEstampadoService
from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.formularios import RectanguloPt


def _png_valido() -> bytes:
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), False)
    pix.clear_with(200)
    return pix.tobytes("png")


def _abrir(ruta: Path) -> tuple[PyMuPDFEstampadoService, str, RegistroDocumentos]:
    registro = RegistroDocumentos()
    repo = PyMuPDFDocumentRepository(registro)
    servicio = PyMuPDFEstampadoService(registro)
    documento = repo.abrir(ruta)
    return servicio, documento.id, registro


def _pdf(tmp_path: Path) -> Path:
    ruta = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page(width=300, height=400)
    doc.save(ruta)
    doc.close()
    return ruta


def test_estampar_inserta_imagen_y_marca_cambios(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))

    servicio.estampar_imagen(doc_id, 0, RectanguloPt(50, 50, 150, 100), _png_valido())

    doc = registro.obtener(doc_id)
    assert len(doc[0].get_images()) == 1
    assert registro.tiene(doc_id, Marca.CAMBIOS_SIN_GUARDAR) is True
    registro.cerrar(doc_id)


def test_estampar_pagina_fuera_de_rango(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))

    with pytest.raises(PaginaFueraDeRango):
        servicio.estampar_imagen(doc_id, 5, RectanguloPt(0, 0, 10, 10), _png_valido())
    registro.cerrar(doc_id)
