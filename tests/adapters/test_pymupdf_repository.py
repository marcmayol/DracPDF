"""Tests de integración del adaptador PyMuPDF con PDFs de fixture reales."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.core.domain.errores import (
    DocumentoNoAbierto,
    DocumentoNoEncontrado,
    FormatoNoSoportado,
    PaginaFueraDeRango,
)


def test_abrir_lee_paginas_y_dimensiones(pdf_simple: Path) -> None:
    repo = PyMuPDFDocumentRepository()

    documento = repo.abrir(pdf_simple)

    assert documento.id
    assert documento.num_paginas == 3
    assert documento.paginas[0].ancho_pt == pytest.approx(595.0, abs=1.0)
    assert documento.paginas[0].alto_pt == pytest.approx(842.0, abs=1.0)
    # Segunda página apaisada.
    assert documento.paginas[1].ancho_pt > documento.paginas[1].alto_pt
    repo.cerrar(documento.id)


def test_renderizar_devuelve_rgba_con_tamano_coherente(pdf_simple: Path) -> None:
    repo = PyMuPDFDocumentRepository()
    documento = repo.abrir(pdf_simple)

    imagen = repo.renderizar_pagina(documento.id, indice=0, escala=1.0)

    assert imagen.ancho_px > 0 and imagen.alto_px > 0
    assert len(imagen.datos) == imagen.ancho_px * imagen.alto_px * 4  # RGBA
    assert imagen.escala == 1.0
    repo.cerrar(documento.id)


def test_mayor_escala_produce_mas_pixeles(pdf_simple: Path) -> None:
    repo = PyMuPDFDocumentRepository()
    documento = repo.abrir(pdf_simple)

    pequena = repo.renderizar_pagina(documento.id, 0, escala=1.0)
    grande = repo.renderizar_pagina(documento.id, 0, escala=2.0)

    assert grande.ancho_px > pequena.ancho_px
    assert grande.alto_px > pequena.alto_px
    repo.cerrar(documento.id)


def test_pagina_fuera_de_rango(pdf_simple: Path) -> None:
    repo = PyMuPDFDocumentRepository()
    documento = repo.abrir(pdf_simple)

    with pytest.raises(PaginaFueraDeRango):
        repo.renderizar_pagina(documento.id, indice=99, escala=1.0)
    repo.cerrar(documento.id)


def test_renderizar_documento_no_abierto() -> None:
    repo = PyMuPDFDocumentRepository()

    with pytest.raises(DocumentoNoAbierto):
        repo.renderizar_pagina("id-inexistente", indice=0, escala=1.0)


def test_abrir_ruta_inexistente(tmp_path: Path) -> None:
    repo = PyMuPDFDocumentRepository()

    with pytest.raises(DocumentoNoEncontrado):
        repo.abrir(tmp_path / "no_existe.pdf")


def test_abrir_fichero_no_pdf(tmp_path: Path) -> None:
    ruta = tmp_path / "falso.pdf"
    ruta.write_text("esto no es un PDF")
    repo = PyMuPDFDocumentRepository()

    with pytest.raises(FormatoNoSoportado):
        repo.abrir(ruta)


def test_cerrar_es_idempotente(pdf_simple: Path) -> None:
    repo = PyMuPDFDocumentRepository()
    documento = repo.abrir(pdf_simple)

    repo.cerrar(documento.id)
    repo.cerrar(documento.id)  # segunda vez no debe fallar
    repo.cerrar("id-desconocido")

    with pytest.raises(DocumentoNoAbierto):
        repo.renderizar_pagina(documento.id, 0, 1.0)
