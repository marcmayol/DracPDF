"""Tests de integración PDF → HTML del adaptador ConversorFitz."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.adapters.pymupdf.conversor import ConversorFitz
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.herramientas import Rango


def _abrir(ruta: Path) -> tuple[ConversorFitz, str]:
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    return ConversorFitz(registro), documento.id


def test_a_html_documento_completo(pdf_titulos_tabla: Path, tmp_path: Path) -> None:
    conversor, doc_id = _abrir(pdf_titulos_tabla)
    destino = tmp_path / "salida.html"

    conversor.a_html(doc_id, destino)

    html = destino.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    # fitz codifica los acentos como entidades HTML; se comprueban subcadenas ASCII.
    assert "Informe de prueba" in html  # título de la página 1
    assert "segunda" in html  # título de la página 2 ("Sección segunda")


def test_a_html_con_rango_limita_paginas(pdf_titulos_tabla: Path, tmp_path: Path) -> None:
    conversor, doc_id = _abrir(pdf_titulos_tabla)
    destino = tmp_path / "rango.html"

    conversor.a_html(doc_id, destino, Rango(1, 1))  # solo la primera página

    html = destino.read_text(encoding="utf-8")
    assert "Informe de prueba" in html
    assert "Sección segunda" not in html


def test_a_html_imagenes_en_carpeta_aneja(pdf_escaneado: Path, tmp_path: Path) -> None:
    conversor, doc_id = _abrir(pdf_escaneado)
    destino = tmp_path / "esc.html"

    conversor.a_html(doc_id, destino, imagenes_embebidas=False)

    carpeta = tmp_path / "esc_imagenes"
    assert carpeta.is_dir()
    assert list(carpeta.glob("img_*"))  # al menos una imagen extraída
    html = destino.read_text(encoding="utf-8")
    assert "data:image" not in html  # ya no van embebidas
    assert "esc_imagenes/" in html  # src reescrito a la carpeta
