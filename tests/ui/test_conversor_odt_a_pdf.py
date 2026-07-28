"""Tests de ODT → PDF: traducción a HTML y conversión con la cadena Qt.

La traducción se prueba en proceso (no necesita fuentes); la conversión completa
corre en subproceso con la plataforma nativa, como el resto de entrantes Qt.
"""

from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path

import fitz
import pytest

from lectorpdf.adapters.qt.odt import odt_a_html
from tests.adapters.generar_fixtures_odt import generar_odt_prueba

_CODIGO = """
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
QApplication([])
from lectorpdf.adapters.qt.conversor_texto import ConversorTextoQt
from lectorpdf.core.domain.conversion import A4
ConversorTextoQt().a_pdf(Path(sys.argv[1]), Path(sys.argv[2]), A4)
"""


def _convertir_nativo(origen: Path, destino: Path) -> subprocess.CompletedProcess[str]:
    entorno = dict(os.environ)
    entorno.pop("QT_QPA_PLATFORM", None)  # plataforma nativa (con fuentes)
    return subprocess.run(
        [sys.executable, "-c", _CODIGO, str(origen), str(destino)],
        env=entorno,
        capture_output=True,
        text=True,
    )


def test_traduce_titulos_formato_listas_y_tablas(tmp_path: Path) -> None:
    odt = generar_odt_prueba(tmp_path / "prueba.odt")

    html = odt_a_html(odt)

    assert "<h1>Informe de prueba</h1>" in html
    assert "<h2>Apartado segundo</h2>" in html
    assert "<b>texto en negrita</b>" in html  # el estilo con nombre, resuelto
    assert "<i>texto en cursiva</i>" in html
    assert html.count("<li>") == 2
    assert "<table" in html and "750 EUR" in html
    assert "data:image/png;base64," in html  # la imagen del paquete, embebida


def test_odt_dañado_da_un_error_con_nombre(tmp_path: Path) -> None:
    falso = tmp_path / "roto.odt"
    falso.write_bytes(b"esto no es un zip")

    with pytest.raises(ValueError, match="roto.odt"):
        odt_a_html(falso)


def test_contenido_xml_ilegible_da_un_error_con_nombre(tmp_path: Path) -> None:
    roto = tmp_path / "malo.odt"
    with zipfile.ZipFile(roto, "w") as paquete:
        paquete.writestr("content.xml", "<office:document-content sin cerrar")

    with pytest.raises(ValueError, match="malo.odt"):
        odt_a_html(roto)


def test_odt_a_pdf_conserva_el_texto(tmp_path: Path) -> None:
    odt = generar_odt_prueba(tmp_path / "prueba.odt")
    destino = tmp_path / "salida.pdf"

    resultado = _convertir_nativo(odt, destino)

    assert resultado.returncode == 0, resultado.stderr
    doc = fitz.open(destino)
    try:
        texto = "\n".join(doc[i].get_text("text") for i in range(doc.page_count))
        fuentes = sum(len(doc.get_page_fonts(i)) for i in range(doc.page_count))
    finally:
        doc.close()

    assert fuentes > 0  # texto real seleccionable, no trazos
    assert "Informe de prueba" in texto
    assert "texto en negrita" in texto
    assert "primer punto" in texto and "segundo punto" in texto
    assert "Alquiler" in texto and "750 EUR" in texto  # la tabla
    assert "año" in texto  # acentos intactos
