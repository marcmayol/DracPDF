"""Tests de RTF → PDF: parser propio y conversión con la cadena Qt."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import fitz
import pytest

from lectorpdf.adapters.qt.rtf import rtf_a_html

# RTF de prueba: tabla de fuentes y colores (que NO deben imprimirse), párrafos,
# negrita, cursiva, subrayado, salto de línea, acentos en \'hh y en \uN.
_RTF = (
    r"{\rtf1\ansi\ansicpg1252\deff0"
    r"{\fonttbl{\f0\fnil\fcharset0 Calibri;}{\f1\fnil Arial;}}"
    r"{\colortbl ;\red255\green0\blue0;}"
    r"{\*\generator DracPDF de prueba;}"
    r"{\info{\title No imprimir este titulo}}"
    r"\viewkind4\uc1\pard\f0\fs22 "
    r"Primer parrafo normal.\par "
    r"Segundo con \b texto en negrita\b0  y \i texto en cursiva\i0  y "
    r"\ul subrayado\ul0 .\par "
    r"Acentos ANSI: a\'f1o, gesti\'f3n.\par "
    r"Unicode: \u8364?uro y \u241?u.\par "
    r"Con salto\line dentro del parrafo.\par"
    r"}"
)

_CODIGO = """
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
QApplication([])
from lectorpdf.adapters.qt.conversor_texto import ConversorTextoQt
from lectorpdf.core.domain.conversion import A4
ConversorTextoQt().a_pdf(Path(sys.argv[1]), Path(sys.argv[2]), A4)
"""


def _rtf_de_prueba(destino: Path) -> Path:
    destino.write_text(_RTF, encoding="latin-1")
    return destino


def _convertir_nativo(origen: Path, destino: Path) -> subprocess.CompletedProcess[str]:
    entorno = dict(os.environ)
    entorno.pop("QT_QPA_PLATFORM", None)  # plataforma nativa (con fuentes)
    return subprocess.run(
        [sys.executable, "-c", _CODIGO, str(origen), str(destino)],
        env=entorno,
        capture_output=True,
        text=True,
    )


def test_traduce_parrafos_y_formato(tmp_path: Path) -> None:
    html = rtf_a_html(_rtf_de_prueba(tmp_path / "prueba.rtf"))

    assert "<b>texto en negrita</b>" in html
    assert "<i>texto en cursiva</i>" in html
    assert "<u>subrayado</u>" in html
    assert html.count("<p>") == 5  # cinco párrafos, el \line no abre uno nuevo
    assert "<br>" in html


def test_descarta_las_tablas_de_control(tmp_path: Path) -> None:
    """Fuentes, colores, generador e info no son texto del documento."""
    html = rtf_a_html(_rtf_de_prueba(tmp_path / "prueba.rtf"))

    assert "Calibri" not in html and "Arial" not in html
    assert "generator" not in html and "DracPDF de prueba" not in html
    assert "No imprimir este titulo" not in html


def test_recupera_los_caracteres_no_ascii(tmp_path: Path) -> None:
    html = rtf_a_html(_rtf_de_prueba(tmp_path / "prueba.rtf"))

    assert "año" in html and "gestión" in html  # \'f1 y \'f3 en cp1252
    assert "€uro" in html and "ñu" in html  # \u8364 y \u241, sin el sustituto
    assert "?uro" not in html


def test_fichero_que_no_es_rtf_da_un_error_con_nombre(tmp_path: Path) -> None:
    falso = tmp_path / "falso.rtf"
    falso.write_text("esto no empieza por la marca de RTF", encoding="utf-8")

    with pytest.raises(ValueError, match="falso.rtf"):
        rtf_a_html(falso)


def test_rtf_a_pdf_conserva_el_texto(tmp_path: Path) -> None:
    origen = _rtf_de_prueba(tmp_path / "prueba.rtf")
    destino = tmp_path / "salida.pdf"

    resultado = _convertir_nativo(origen, destino)

    assert resultado.returncode == 0, resultado.stderr
    doc = fitz.open(destino)
    try:
        texto = "\n".join(doc[i].get_text("text") for i in range(doc.page_count))
        fuentes = sum(len(doc.get_page_fonts(i)) for i in range(doc.page_count))
    finally:
        doc.close()

    assert fuentes > 0  # texto real seleccionable
    assert "Primer parrafo normal." in texto
    assert "texto en negrita" in texto
    assert "año" in texto and "€uro" in texto
    assert "Calibri" not in texto  # la tabla de fuentes no se imprime
