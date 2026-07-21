"""Tests de los casos de uso de conversión con fakes de los puertos."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.conversion import A4
from lectorpdf.core.domain.errores import ErrorDominio
from lectorpdf.core.domain.herramientas import Rango
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.convertir_a_html import ConvertirAHtml
from lectorpdf.core.use_cases.convertir_a_markdown import ConvertirAMarkdown
from lectorpdf.core.use_cases.convertir_a_word import ConvertirAWord
from lectorpdf.core.use_cases.convertir_word_a_pdf import ConvertirWordAPdf
from lectorpdf.core.use_cases.es_pdf_escaneado import EsPdfEscaneado
from tests.core.fakes import FakeConversorPDF, FakeConversorWord


def _documento() -> Documento:
    return Documento(id="doc-1", ruta=Path("d.pdf"), paginas=(Pagina(0, 400.0, 600.0),))


def test_convertir_a_word_delega_con_rango(tmp_path: Path) -> None:
    conversor = FakeConversorPDF()
    destino = tmp_path / "s.docx"

    ConvertirAWord(conversor).ejecutar(_documento(), destino, Rango(1, 2))

    assert conversor.word == [("doc-1", destino, Rango(1, 2))]


def test_convertir_a_html_pasa_opcion_de_imagenes(tmp_path: Path) -> None:
    conversor = FakeConversorPDF()
    destino = tmp_path / "s.html"

    ConvertirAHtml(conversor).ejecutar(
        _documento(), destino, imagenes_embebidas=False
    )

    assert conversor.html == [("doc-1", destino, None, False)]


def test_convertir_a_markdown_delega(tmp_path: Path) -> None:
    conversor = FakeConversorPDF()
    destino = tmp_path / "s.md"

    ConvertirAMarkdown(conversor).ejecutar(_documento(), destino)

    assert conversor.markdown == [("doc-1", destino, None)]


def test_es_pdf_escaneado_delega() -> None:
    assert EsPdfEscaneado(FakeConversorPDF(escaneado=True)).ejecutar(_documento())
    assert not EsPdfEscaneado(FakeConversorPDF(escaneado=False)).ejecutar(_documento())


def test_word_a_pdf_delega(tmp_path: Path) -> None:
    conversor = FakeConversorWord()
    docx = tmp_path / "e.docx"
    destino = tmp_path / "s.pdf"

    ConvertirWordAPdf(conversor).ejecutar(docx, destino, A4)

    assert conversor.conversiones == [(docx, destino)]


def test_word_a_pdf_rechaza_no_docx(tmp_path: Path) -> None:
    conversor = FakeConversorWord()

    with pytest.raises(ErrorDominio):
        ConvertirWordAPdf(conversor).ejecutar(tmp_path / "x.txt", tmp_path / "s.pdf", A4)
    assert conversor.conversiones == []
