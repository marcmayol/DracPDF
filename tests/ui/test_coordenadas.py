"""Tests de la transformación puntos PDF -> escena (sin Qt)."""

from __future__ import annotations

from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.ui.forms.coordenadas import rect_pdf_a_escena


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
