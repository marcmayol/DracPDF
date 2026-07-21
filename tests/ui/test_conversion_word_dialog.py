"""Tests del diálogo de Word → PDF (etiquetado honesto y config)."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel

from lectorpdf.ui.conversion.word_dialog import ConversionWordDialog


def test_config_por_defecto_es_a4_con_margen_20(qapp: object) -> None:
    dialogo = ConversionWordDialog()
    config = dialogo.config()

    assert (config.ancho_mm, config.alto_mm) == (210.0, 297.0)  # A4
    assert config.margen_mm == 20.0


def test_config_refleja_carta_y_margen(qapp: object) -> None:
    dialogo = ConversionWordDialog()
    dialogo._tamano.setCurrentText("Carta")
    dialogo._margen.setValue(10)

    config = dialogo.config()

    assert (config.ancho_mm, config.alto_mm) == (215.9, 279.4)  # Carta
    assert config.margen_mm == 10.0


def test_muestra_el_aviso_de_reformateado(qapp: object) -> None:
    dialogo = ConversionWordDialog()
    textos = " ".join(lbl.text() for lbl in dialogo.findChildren(QLabel))
    assert "no el diseño exacto" in textos
