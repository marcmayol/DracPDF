"""Tests de integración PDF → Markdown del adaptador ConversorFitz."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.adapters.pymupdf.conversor import ConversorFitz
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos


def _abrir(ruta: Path) -> tuple[ConversorFitz, str]:
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    return ConversorFitz(registro), documento.id


def test_a_markdown_titulos_texto_y_tabla(pdf_titulos_tabla: Path, tmp_path: Path) -> None:
    conversor, doc_id = _abrir(pdf_titulos_tabla)
    destino = tmp_path / "salida.md"

    conversor.a_markdown(doc_id, destino)

    md = destino.read_text(encoding="utf-8")
    lineas = md.splitlines()

    # Título detectado por tamaño de fuente relativo (empieza por #).
    assert any(
        ln.startswith("#") and "Informe de prueba" in ln for ln in lineas
    ), md
    # Texto de cuerpo presente.
    assert "Resumen ejecutivo del documento." in md
    # Tabla en formato de tuberías, con su fila separadora y las celdas.
    assert "| --- |" in md
    assert "Ingresos" in md and "1000" in md


def test_a_markdown_sin_texto_queda_practicamente_vacio(
    pdf_escaneado: Path, tmp_path: Path
) -> None:
    conversor, doc_id = _abrir(pdf_escaneado)
    destino = tmp_path / "esc.md"

    conversor.a_markdown(doc_id, destino)

    # Un escaneo sin capa de texto no produce contenido (solo el salto final).
    assert destino.read_text(encoding="utf-8").strip() == ""


def test_es_escaneado_detecta_pdf_sin_texto(
    pdf_escaneado: Path, pdf_titulos_tabla: Path
) -> None:
    conv_esc, id_esc = _abrir(pdf_escaneado)
    assert conv_esc.es_escaneado(id_esc) is True

    conv_txt, id_txt = _abrir(pdf_titulos_tabla)
    assert conv_txt.es_escaneado(id_txt) is False
