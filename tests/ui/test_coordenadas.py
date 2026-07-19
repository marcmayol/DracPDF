"""Tests de la transformación puntos PDF -> escena (sin Qt)."""

from __future__ import annotations

import pytest

from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.ui.forms.coordenadas import (
    RectEscena,
    rect_escena_a_pdf,
    rect_pdf_a_escena,
)


def test_traslada_por_origen_y_escala_unitaria() -> None:
    rect_pt = RectanguloPt(50, 60, 250, 80)

    r = rect_pdf_a_escena(rect_pt, origen_x=12, origen_y=100, escala=1.0)

    assert (r.x, r.y) == (62, 160)
    assert (r.ancho, r.alto) == (200, 20)


def test_escala_multiplica_posicion_y_tamano() -> None:
    rect_pt = RectanguloPt(50, 60, 250, 80)

    r = rect_pdf_a_escena(rect_pt, origen_x=0, origen_y=0, escala=2.0)

    assert (r.x, r.y) == (100, 120)
    assert (r.ancho, r.alto) == (400, 40)


def test_inversa_recupera_los_puntos_pdf() -> None:
    r = RectEscena(x=112, y=220, ancho=400, alto=40)

    rect_pt = rect_escena_a_pdf(r, origen_x=12, origen_y=100, escala=2.0)

    assert (rect_pt.x0, rect_pt.y0) == (50, 60)
    assert (rect_pt.x1, rect_pt.y1) == (250, 80)


def test_ida_y_vuelta_es_identidad() -> None:
    original = RectanguloPt(30, 40, 130, 90)

    escena = rect_pdf_a_escena(original, origen_x=5, origen_y=8, escala=1.7)
    vuelta = rect_escena_a_pdf(escena, origen_x=5, origen_y=8, escala=1.7)

    assert (vuelta.x0, vuelta.y0, vuelta.x1, vuelta.y1) == pytest.approx(
        (original.x0, original.y0, original.x1, original.y1)
    )
