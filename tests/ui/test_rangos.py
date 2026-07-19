"""Tests del parser de rangos de páginas (sin Qt)."""

from __future__ import annotations

import pytest

from lectorpdf.core.domain.herramientas import Rango
from lectorpdf.ui.herramientas.rangos import parsear_rangos


def test_parsea_rangos_y_paginas_sueltas() -> None:
    assert parsear_rangos("1-3, 4-8, 10") == [Rango(1, 3), Rango(4, 8), Rango(10, 10)]


def test_ignora_espacios_y_admite_punto_y_coma() -> None:
    assert parsear_rangos(" 2 ; 5-6 ") == [Rango(2, 2), Rango(5, 6)]


def test_texto_vacio_es_error() -> None:
    with pytest.raises(ValueError):
        parsear_rangos("   ")


def test_rango_invertido_es_error() -> None:
    with pytest.raises(ValueError):
        parsear_rangos("5-2")
