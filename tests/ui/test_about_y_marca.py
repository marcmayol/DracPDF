"""Tests del diálogo 'Acerca de' y del localizador de assets de marca."""

from __future__ import annotations

from lectorpdf.ui.about_dialog import AboutDialog
from lectorpdf.ui.theme import marca


def test_about_muestra_el_nombre_de_la_app(qapp: object) -> None:
    dialogo = AboutDialog(es_oscuro=True)

    assert marca.NOMBRE_APP == "DracPDF"
    assert marca.NOMBRE_APP in dialogo.windowTitle()


def test_about_se_construye_sin_logo(qapp: object) -> None:
    # Aunque el logo aún no esté descargado, el diálogo debe construirse.
    claro = AboutDialog(es_oscuro=False)
    oscuro = AboutDialog(es_oscuro=True)

    assert claro is not None and oscuro is not None


def test_marca_devuelve_none_o_ruta_existente() -> None:
    # No falla aunque los assets no estén; si están, la ruta existe.
    for valor in (marca.ruta_icono_app(), marca.ruta_logo(True), marca.ruta_logo(False)):
        assert valor is None or valor.is_file()
