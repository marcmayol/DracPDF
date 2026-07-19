"""Tests de los tokens de la identidad "Ladón" (sin Qt)."""

from __future__ import annotations

import re
from dataclasses import fields

import pytest

from lectorpdf.ui.theme import tokens

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_CAMPOS_COLOR = [
    "canvas",
    "bg",
    "surface",
    "surface_2",
    "border",
    "text",
    "text_muted",
    "accent",
    "accent_hover",
    "on_accent",
    "sig_valid",
    "sig_invalid",
    "sig_unknown",
]


@pytest.mark.parametrize("tema", [tokens.TEMA_OSCURO, tokens.TEMA_CLARO])
def test_todos_los_colores_son_hex_validos(tema: tokens.Tema) -> None:
    for campo in _CAMPOS_COLOR:
        valor = getattr(tema, campo)
        assert _HEX.match(valor), f"{tema.nombre}.{campo} = {valor!r} no es hex"


def test_hay_dos_temas_y_el_por_defecto_es_oscuro() -> None:
    assert set(tokens.TEMAS) == {"claro", "oscuro"}
    assert tokens.TEMA_POR_DEFECTO.nombre == "oscuro"
    assert tokens.TEMA_POR_DEFECTO.es_oscuro is True


def test_los_dos_temas_definen_los_mismos_campos() -> None:
    campos = {f.name for f in fields(tokens.Tema)}
    assert campos == {f.name for f in fields(tokens.TEMA_CLARO)}
    # Ambos temas comparten estructura; difieren en valores.
    assert tokens.TEMA_OSCURO.accent != tokens.TEMA_CLARO.accent


def test_tema_por_nombre_cae_al_por_defecto_si_no_existe() -> None:
    assert tokens.tema_por_nombre("claro") is tokens.TEMA_CLARO
    assert tokens.tema_por_nombre("inexistente") is tokens.TEMA_POR_DEFECTO


def test_rgba_deriva_del_hex() -> None:
    assert tokens.rgba("#E0534A", 0.30) == "rgba(224, 83, 74, 0.3)"
    assert tokens.rgba("#FFFFFF", 1.0) == "rgba(255, 255, 255, 1.0)"
