"""Tests de la carga y recoloreado de iconos SVG por tema."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QIcon

from lectorpdf.ui.theme import tokens
from lectorpdf.ui.theme.iconos import icono

_NOMBRES = [
    "open",
    "save",
    "zoom-in",
    "zoom-out",
    "page-prev",
    "page-next",
    "form-fill",
    "sign-draw",
    "sign-cert",
    "verify",
]


@pytest.mark.parametrize("nombre", _NOMBRES)
def test_cada_icono_carga_y_no_esta_vacio(qapp: object, nombre: str) -> None:
    ico = icono(nombre, tokens.TEMA_OSCURO.text)

    assert isinstance(ico, QIcon)
    assert not ico.isNull()
    assert not ico.pixmap(20, 20).isNull()


def test_recolorear_produce_pixmaps_distintos_por_color(qapp: object) -> None:
    claro = icono("verify", tokens.TEMA_CLARO.text).pixmap(20, 20).toImage()
    accent = icono("verify", tokens.TEMA_OSCURO.accent).pixmap(20, 20).toImage()

    assert claro != accent  # el color del trazo cambia el render


def test_icono_inexistente_lanza(qapp: object) -> None:
    with pytest.raises(FileNotFoundError):
        icono("no-existe", tokens.TEMA_OSCURO.text)
