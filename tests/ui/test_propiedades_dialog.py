"""Tests del diálogo de propiedades y del formateo de tamaño."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.contenido import PropiedadesDocumento
from lectorpdf.ui.propiedades_dialog import PropiedadesDialog, formatear_tamano


def test_formatear_tamano() -> None:
    assert formatear_tamano(512) == "512 B"
    assert formatear_tamano(1536) == "1.5 KB"
    assert formatear_tamano(5 * 1024 * 1024) == "5.0 MB"
    assert formatear_tamano(3 * 1024**3) == "3.0 GB"


def _props(cifrado: bool = False) -> PropiedadesDocumento:
    return PropiedadesDocumento(
        titulo="Mi Título",
        autor="Yo",
        asunto="",
        palabras_clave="",
        creador="",
        productor="",
        version_pdf="PDF 1.7",
        cifrado=cifrado,
        num_paginas=5,
        tamano_bytes=2048,
    )


def test_dialogo_muestra_los_datos(qapp: object) -> None:
    from PySide6.QtWidgets import QLabel

    dialogo = PropiedadesDialog(_props(cifrado=True), Path("C:/docs/mi.pdf"))
    textos = [lbl.text() for lbl in dialogo.findChildren(QLabel)]

    assert "Mi Título" in textos
    assert "PDF 1.7" in textos
    assert "5" in textos  # páginas
    assert "Sí" in textos  # cifrado
    assert "2.0 KB" in textos
    assert "mi.pdf" in textos
