"""Test de integración Word → PDF (mammoth + Qt).

El texto seleccionable exige una plataforma Qt con fuentes; la plataforma
`offscreen` de la suite no tiene ninguna (rasteriza el texto como trazos). Por eso
la conversión se ejecuta en un subproceso con la plataforma NATIVA (con fuentes),
y luego se verifica el PDF con fitz.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import fitz

from tests.adapters.generar_fixtures_docx import generar_docx_prueba

_CODIGO = """
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
QApplication([])
from lectorpdf.adapters.qt.conversor_word import ConversorWordQt
from lectorpdf.core.domain.conversion import A4
ConversorWordQt().a_pdf(Path(sys.argv[1]), Path(sys.argv[2]), A4)
"""


def _convertir_nativo(docx: Path, destino: Path) -> subprocess.CompletedProcess[str]:
    entorno = dict(os.environ)
    entorno.pop("QT_QPA_PLATFORM", None)  # plataforma nativa (con fuentes)
    return subprocess.run(
        [sys.executable, "-c", _CODIGO, str(docx), str(destino)],
        env=entorno,
        capture_output=True,
        text=True,
    )


def test_word_a_pdf_texto_seleccionable_y_tabla(tmp_path: Path) -> None:
    docx = generar_docx_prueba(tmp_path / "prueba.docx")
    destino = tmp_path / "salida.pdf"

    resultado = _convertir_nativo(docx, destino)
    assert resultado.returncode == 0, resultado.stderr
    assert destino.is_file()

    doc = fitz.open(destino)
    texto = "\n".join(doc[i].get_text("text") for i in range(doc.page_count))
    fuentes = sum(len(doc.get_page_fonts(i)) for i in range(doc.page_count))
    doc.close()

    assert fuentes > 0  # texto real con fuentes (seleccionable), no trazos
    assert "Contrato de arrendamiento" in texto  # título
    assert "texto en negrita" in texto
    assert "cláusula" in texto  # de la lista
    assert "Renta mensual" in texto and "750 EUR" in texto  # tabla renderizada
