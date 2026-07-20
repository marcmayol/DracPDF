"""Tests de impresión: pintado del documento sobre un QPrinter a PDF."""

from __future__ import annotations

from pathlib import Path

import fitz
from PySide6.QtPrintSupport import QPrinter

from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.impresion.impresion import imprimir_documento
from tests.core.fakes import FakeDocumentRepository


def _documento(num_paginas: int = 4) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(
            Pagina(indice=i, ancho_pt=595.0, alto_pt=842.0)
            for i in range(num_paginas)
        ),
    )


def _render() -> RenderizarPagina:
    imagen = ImagenRenderizada(
        ancho_px=200, alto_px=283, datos=b"\xff" * (200 * 283 * 4), escala=1.0
    )
    return RenderizarPagina(FakeDocumentRepository(_documento(), imagen))


def _printer(destino: Path) -> QPrinter:
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(destino))
    printer.setResolution(150)
    return printer


def test_imprime_el_rango_pedido(qapp: object, tmp_path: Path) -> None:
    destino = tmp_path / "salida.pdf"
    printer = _printer(destino)

    # Rango 2..3 (0-based, inclusive) -> 2 páginas.
    pintadas = imprimir_documento(printer, _documento(), _render(), 1, 2)

    assert pintadas == 2
    doc = fitz.open(destino)
    assert doc.page_count == 2
    doc.close()


def test_imprime_documento_completo(qapp: object, tmp_path: Path) -> None:
    destino = tmp_path / "todo.pdf"
    printer = _printer(destino)

    pintadas = imprimir_documento(printer, _documento(4), _render(), 0, 3)

    assert pintadas == 4
    doc = fitz.open(destino)
    assert doc.page_count == 4
    doc.close()


def test_rango_fuera_de_limites_se_acota(qapp: object, tmp_path: Path) -> None:
    destino = tmp_path / "acotado.pdf"
    printer = _printer(destino)

    # ultima pedida (10) se acota a la última real (3) -> 4 páginas.
    pintadas = imprimir_documento(printer, _documento(4), _render(), 0, 10)

    assert pintadas == 4
