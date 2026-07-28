"""Tests de PDF → ODT y PDF → RTF.

La prueba fuerte es la ida y vuelta: lo que escribe el generador lo vuelve a
leer el lector de la Parte B (odt_a_html / rtf_a_html) y el texto sobrevive.
"""

from __future__ import annotations

import zipfile
from html import unescape
from pathlib import Path

import fitz

from lectorpdf.adapters.pymupdf.conversor import ConversorFitz
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.adapters.qt.odt import odt_a_html
from lectorpdf.adapters.qt.rtf import rtf_a_html
from lectorpdf.core.domain.herramientas import Rango

_TITULO = "Informe anual"
_PARRAFO = "Un párrafo con acentos: año, gestión, ñu."


def _pdf(destino: Path) -> Path:
    """PDF con un título grande, un párrafo y una tabla con líneas."""
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.insert_text((60, 80), _TITULO, fontsize=24)
    pagina.insert_text((60, 130), _PARRAFO, fontsize=11)
    filas = [["Concepto", "Importe"], ["Alquiler", "750,00"]]
    for f, fila in enumerate(filas):
        for c, celda in enumerate(fila):
            rect = fitz.Rect(60 + c * 150, 200 + f * 24, 60 + (c + 1) * 150, 224 + f * 24)
            pagina.draw_rect(rect, color=(0, 0, 0), width=0.7)
            pagina.insert_text((rect.x0 + 4, rect.y1 - 8), celda, fontsize=10)
    segunda = doc.new_page(width=595, height=842)
    segunda.insert_text((60, 80), "Solo en la segunda página", fontsize=11)
    doc.save(destino)
    doc.close()
    return destino


def _conversor(ruta: Path) -> tuple[ConversorFitz, str]:
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    return ConversorFitz(registro), documento.id


def test_odt_es_un_paquete_valido_y_se_relee(tmp_path: Path) -> None:
    conversor, doc_id = _conversor(_pdf(tmp_path / "d.pdf"))
    destino = tmp_path / "salida.odt"

    conversor.a_odt(doc_id, destino)

    with zipfile.ZipFile(destino) as paquete:
        nombres = paquete.namelist()
        # La especificación ODF exige el mimetype primero y sin comprimir.
        assert nombres[0] == "mimetype"
        assert paquete.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert paquete.read("mimetype").decode() == (
            "application/vnd.oasis.opendocument.text"
        )
        assert "META-INF/manifest.xml" in nombres and "content.xml" in nombres

    html = odt_a_html(destino)  # el lector de la Parte B lo entiende
    assert _TITULO in html
    assert "año, gestión, ñu" in html
    assert "<table" in html and "750,00" in html


def test_rtf_es_ascii_y_se_relee(tmp_path: Path) -> None:
    conversor, doc_id = _conversor(_pdf(tmp_path / "d.pdf"))
    destino = tmp_path / "salida.rtf"

    conversor.a_rtf(doc_id, destino)

    crudo = destino.read_bytes()
    assert crudo.startswith(b"{\\rtf1")
    crudo.decode("ascii")  # todo lo no ASCII va escapado: si no, revienta aquí

    html = unescape(rtf_a_html(destino))  # el parser de la Parte B lo entiende
    assert _TITULO in html
    assert "año, gestión, ñu" in html
    assert "750,00" in html  # la tabla, aunque el parser la lea como párrafos


def test_respetan_el_rango_de_paginas(tmp_path: Path) -> None:
    conversor, doc_id = _conversor(_pdf(tmp_path / "d.pdf"))
    odt = tmp_path / "solo1.odt"
    rtf = tmp_path / "solo1.rtf"

    conversor.a_odt(doc_id, odt, Rango(1, 1))
    conversor.a_rtf(doc_id, rtf, Rango(1, 1))

    assert "Solo en la segunda página" not in odt_a_html(odt)
    assert "Solo en la segunda" not in unescape(rtf_a_html(rtf))


def test_reportan_progreso_por_pagina(tmp_path: Path) -> None:
    conversor, doc_id = _conversor(_pdf(tmp_path / "d.pdf"))
    avances: list[tuple[int, int]] = []

    conversor.a_odt(
        doc_id, tmp_path / "s.odt", None, lambda h, t: avances.append((h, t))
    )

    assert avances == [(1, 2), (2, 2)]
