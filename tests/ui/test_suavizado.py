"""Tests del suavizado Catmull-Rom -> Bézier (sin Qt)."""

from __future__ import annotations

import pytest

from lectorpdf.ui.signature.suavizado import curva_catmull_rom


def test_menos_de_dos_puntos_no_produce_segmentos() -> None:
    assert curva_catmull_rom([]) == []
    assert curva_catmull_rom([(1.0, 2.0)]) == []


def test_n_puntos_producen_n_menos_1_segmentos() -> None:
    puntos = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)]

    segmentos = curva_catmull_rom(puntos)

    assert len(segmentos) == 3


def test_dos_puntos_controles_sobre_la_recta() -> None:
    # Segmento único: p0=p1=(0,0), p3=p2=(6,0).
    # c1 = (0,0) + ((6,0)-(0,0))/6 = (1,0); c2 = (6,0) - ((6,0)-(0,0))/6 = (5,0)
    (inicio, c1, c2, fin) = curva_catmull_rom([(0.0, 0.0), (6.0, 0.0)])[0]

    assert inicio == (0.0, 0.0)
    assert fin == (6.0, 0.0)
    assert c1 == pytest.approx((1.0, 0.0))
    assert c2 == pytest.approx((5.0, 0.0))


def test_puntos_colineales_dan_controles_colineales() -> None:
    # Recta diagonal y = x: todos los controles deben cumplir cx == cy.
    puntos = [(0.0, 0.0), (2.0, 2.0), (4.0, 4.0), (6.0, 6.0)]

    for _, c1, c2, _ in curva_catmull_rom(puntos):
        assert c1[0] == pytest.approx(c1[1])
        assert c2[0] == pytest.approx(c2[1])
