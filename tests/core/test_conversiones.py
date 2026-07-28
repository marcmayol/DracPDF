"""Tests de los casos de uso de conversión con fakes de los puertos."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.conversion import A4, AjusteImagen
from lectorpdf.core.domain.errores import DocumentoNoEncontrado, ErrorDominio
from lectorpdf.core.domain.herramientas import Rango
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.convertir_a_html import ConvertirAHtml
from lectorpdf.core.use_cases.convertir_a_markdown import ConvertirAMarkdown
from lectorpdf.core.use_cases.convertir_a_word import ConvertirAWord
from lectorpdf.core.use_cases.convertir_imagenes_a_pdf import ConvertirImagenesAPdf
from lectorpdf.core.use_cases.convertir_texto_a_pdf import ConvertirTextoAPdf
from lectorpdf.core.use_cases.convertir_word_a_pdf import ConvertirWordAPdf
from lectorpdf.core.use_cases.es_pdf_escaneado import EsPdfEscaneado
from tests.core.fakes import (
    FakeConversorImagenes,
    FakeConversorPDF,
    FakeConversorTexto,
    FakeConversorWord,
)


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


def _imagenes(tmp_path: Path, *nombres: str) -> list[Path]:
    rutas = []
    for nombre in nombres:
        ruta = tmp_path / nombre
        ruta.write_bytes(b"no importa: el caso de uso no abre el fichero")
        rutas.append(ruta)
    return rutas


def test_imagenes_a_pdf_respeta_el_orden_recibido(tmp_path: Path) -> None:
    conversor = FakeConversorImagenes()
    rutas = _imagenes(tmp_path, "b.png", "a.jpg", "c.tiff")
    destino = tmp_path / "s.pdf"

    ConvertirImagenesAPdf(conversor).ejecutar(rutas, destino)

    convertidas, salida, ajuste = conversor.conversiones[0]
    assert convertidas == tuple(rutas)  # el orden lo decide quien llama
    assert salida == destino
    assert ajuste is AjusteImagen.TAMANO_IMAGEN  # por defecto


def test_imagenes_a_pdf_rechaza_lista_vacia(tmp_path: Path) -> None:
    conversor = FakeConversorImagenes()

    with pytest.raises(ErrorDominio):
        ConvertirImagenesAPdf(conversor).ejecutar([], tmp_path / "s.pdf")
    assert conversor.conversiones == []


def test_imagenes_a_pdf_rechaza_formato_no_admitido(tmp_path: Path) -> None:
    conversor = FakeConversorImagenes()
    rutas = _imagenes(tmp_path, "a.png", "documento.docx")

    with pytest.raises(ErrorDominio):
        ConvertirImagenesAPdf(conversor).ejecutar(rutas, tmp_path / "s.pdf")
    assert conversor.conversiones == []  # ni una sola imagen se convierte


@pytest.mark.parametrize(
    "nombre", ["notas.md", "pagina.HTML", "leeme.txt", "informe.odt"]
)
def test_texto_a_pdf_admite_markdown_html_y_txt(tmp_path: Path, nombre: str) -> None:
    conversor = FakeConversorTexto()
    origen = tmp_path / nombre
    origen.write_text("contenido", encoding="utf-8")
    destino = tmp_path / "s.pdf"

    ConvertirTextoAPdf(conversor).ejecutar(origen, destino)

    assert conversor.conversiones == [(origen, destino)]


def test_texto_a_pdf_rechaza_otras_extensiones(tmp_path: Path) -> None:
    conversor = FakeConversorTexto()
    origen = tmp_path / "hoja.csv"
    origen.write_text("a;b", encoding="utf-8")

    with pytest.raises(ErrorDominio):
        ConvertirTextoAPdf(conversor).ejecutar(origen, tmp_path / "s.pdf")
    assert conversor.conversiones == []


def test_texto_a_pdf_rechaza_fichero_inexistente(tmp_path: Path) -> None:
    conversor = FakeConversorTexto()

    with pytest.raises(DocumentoNoEncontrado):
        ConvertirTextoAPdf(conversor).ejecutar(tmp_path / "no.md", tmp_path / "s.pdf")
    assert conversor.conversiones == []


def test_imagenes_a_pdf_rechaza_fichero_inexistente(tmp_path: Path) -> None:
    conversor = FakeConversorImagenes()

    with pytest.raises(DocumentoNoEncontrado):
        ConvertirImagenesAPdf(conversor).ejecutar(
            [tmp_path / "fantasma.png"], tmp_path / "s.pdf"
        )
    assert conversor.conversiones == []
