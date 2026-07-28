"""Tests de integración de Markdown / HTML / texto plano → PDF (Qt).

Como en Word → PDF, la conversión corre en un subproceso con la plataforma Qt
nativa: bajo `offscreen` no hay fuentes y el PDF saldría sin texto real.
Los ficheros de entrada se generan aquí: nada de binarios en el repo.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import fitz

from lectorpdf.adapters.qt.conversor_texto import ConversorTextoQt, leer_texto
from lectorpdf.core.domain.conversion import A4

_CODIGO = """
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
QApplication([])
from lectorpdf.adapters.qt.conversor_texto import ConversorTextoQt
from lectorpdf.core.domain.conversion import ConfigPagina
config = ConfigPagina(
    ancho_mm=float(sys.argv[3]),
    alto_mm=float(sys.argv[4]),
    margen_mm=float(sys.argv[5]),
)
ConversorTextoQt().a_pdf(Path(sys.argv[1]), Path(sys.argv[2]), config)
"""


def _convertir_nativo(
    origen: Path,
    destino: Path,
    ancho: float = 210.0,
    alto: float = 297.0,
    margen: float = 20.0,
) -> subprocess.CompletedProcess[str]:
    entorno = dict(os.environ)
    entorno.pop("QT_QPA_PLATFORM", None)  # plataforma nativa (con fuentes)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            _CODIGO,
            str(origen),
            str(destino),
            str(ancho),
            str(alto),
            str(margen),
        ],
        env=entorno,
        capture_output=True,
        text=True,
    )


def _texto_del_pdf(ruta: Path) -> str:
    doc = fitz.open(ruta)
    try:
        return "\n".join(doc[i].get_text("text") for i in range(doc.page_count))
    finally:
        doc.close()


def test_markdown_conserva_texto_titulos_y_listas(tmp_path: Path) -> None:
    origen = tmp_path / "notas.md"
    origen.write_text(
        "# Título principal\n\nUn párrafo con **negrita**.\n\n- uno\n- dos\n",
        encoding="utf-8",
    )
    destino = tmp_path / "notas.pdf"

    resultado = _convertir_nativo(origen, destino)

    assert resultado.returncode == 0, resultado.stderr
    texto = _texto_del_pdf(destino)
    assert "Título principal" in texto
    assert "negrita" in texto  # el marcado no se cuela como asteriscos
    assert "**" not in texto
    assert "uno" in texto and "dos" in texto


def test_html_se_interpreta_no_se_escribe_literal(tmp_path: Path) -> None:
    origen = tmp_path / "pagina.html"
    origen.write_text(
        "<h1>Cabecera</h1><p>Párrafo con <em>énfasis</em>.</p>", encoding="utf-8"
    )
    destino = tmp_path / "pagina.pdf"

    resultado = _convertir_nativo(origen, destino)

    assert resultado.returncode == 0, resultado.stderr
    texto = _texto_del_pdf(destino)
    assert "Cabecera" in texto
    assert "énfasis" in texto
    assert "<p>" not in texto


def test_texto_plano_no_interpreta_el_marcado(tmp_path: Path) -> None:
    origen = tmp_path / "plano.txt"
    origen.write_text("# Esto no es un título\n<b>ni negrita</b>", encoding="utf-8")
    destino = tmp_path / "plano.pdf"

    resultado = _convertir_nativo(origen, destino)

    assert resultado.returncode == 0, resultado.stderr
    texto = _texto_del_pdf(destino)
    assert "# Esto no es un título" in texto
    assert "<b>ni negrita</b>" in texto  # tal cual, sin interpretar


def test_pagina_y_margenes_configurables(tmp_path: Path) -> None:
    origen = tmp_path / "n.md"
    origen.write_text("texto", encoding="utf-8")
    destino = tmp_path / "n.pdf"

    resultado = _convertir_nativo(origen, destino, ancho=148.0, alto=210.0, margen=10.0)

    assert resultado.returncode == 0, resultado.stderr
    doc = fitz.open(destino)
    try:
        assert round(doc[0].rect.width) == round(148.0 * 72 / 25.4)
        assert round(doc[0].rect.height) == round(210.0 * 72 / 25.4)
    finally:
        doc.close()


def test_texto_en_cp1252_no_revienta(tmp_path: Path) -> None:
    """Los .txt guardados por programas de Windows no vienen en UTF-8."""
    origen = tmp_path / "ansi.txt"
    origen.write_bytes("Año de gestión: ñ, á, ü".encode("cp1252"))

    assert leer_texto(origen) == "Año de gestión: ñ, á, ü"


def test_reporta_progreso(qapp: object, tmp_path: Path) -> None:
    origen = tmp_path / "n.txt"
    origen.write_text("texto", encoding="utf-8")
    avances: list[tuple[int, int]] = []

    ConversorTextoQt().a_pdf(
        origen, tmp_path / "n.pdf", A4, lambda h, t: avances.append((h, t))
    )

    assert avances == [(1, 1)]
