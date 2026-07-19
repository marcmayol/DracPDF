"""Tests del caso de uso AbrirDocumento con un fake del repositorio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.errores import DocumentoNoEncontrado, FormatoNoSoportado
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.abrir_documento import AbrirDocumento
from tests.core.fakes import FakeDocumentRepository


def _documento(ruta: Path) -> Documento:
    return Documento(
        id="doc-1",
        ruta=ruta,
        paginas=(Pagina(indice=0, ancho_pt=595.0, alto_pt=842.0),),
        titulo="Prueba",
    )


def test_abre_pdf_existente_y_delega_en_el_repositorio(tmp_path: Path) -> None:
    ruta = tmp_path / "doc.pdf"
    ruta.write_bytes(b"%PDF-1.7\n")
    esperado = _documento(ruta)
    repo = FakeDocumentRepository(documento=esperado)

    resultado = AbrirDocumento(repo).ejecutar(ruta)

    assert resultado is esperado
    assert repo.abrir_llamado_con == ruta


def test_ruta_inexistente_lanza_documento_no_encontrado(tmp_path: Path) -> None:
    repo = FakeDocumentRepository()

    with pytest.raises(DocumentoNoEncontrado):
        AbrirDocumento(repo).ejecutar(tmp_path / "no_existe.pdf")

    assert repo.abrir_llamado_con is None


def test_extension_no_pdf_lanza_formato_no_soportado(tmp_path: Path) -> None:
    ruta = tmp_path / "doc.txt"
    ruta.write_text("no soy un pdf")
    repo = FakeDocumentRepository()

    with pytest.raises(FormatoNoSoportado):
        AbrirDocumento(repo).ejecutar(ruta)

    assert repo.abrir_llamado_con is None


def test_directorio_con_extension_pdf_no_se_considera_documento(tmp_path: Path) -> None:
    ruta = tmp_path / "carpeta.pdf"
    ruta.mkdir()
    repo = FakeDocumentRepository()

    with pytest.raises(DocumentoNoEncontrado):
        AbrirDocumento(repo).ejecutar(ruta)
