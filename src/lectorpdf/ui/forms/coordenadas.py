"""Traducción de coordenadas de campo: puntos PDF -> coordenadas de escena.

Función pura, sin Qt, para poder testearla aislada. PyMuPDF entrega los rects de
los widgets con origen arriba-izquierda (igual que la escena), así que el mapeo
es una traslación por el origen de la página más un escalado por el zoom.
"""

from __future__ import annotations

from dataclasses import dataclass

from lectorpdf.core.domain.formularios import RectanguloPt


@dataclass(frozen=True)
class RectEscena:
    x: float
    y: float
    ancho: float
    alto: float


def rect_pdf_a_escena(
    rect_pt: RectanguloPt, origen_x: float, origen_y: float, escala: float
) -> RectEscena:
    """Mapea un rect de campo (puntos PDF) a la escena, dado el origen (esquina
    superior izquierda) de su página en la escena y la escala de render."""
    return RectEscena(
        x=origen_x + rect_pt.x0 * escala,
        y=origen_y + rect_pt.y0 * escala,
        ancho=rect_pt.ancho * escala,
        alto=rect_pt.alto * escala,
    )
