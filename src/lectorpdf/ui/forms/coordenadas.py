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


def rect_escena_a_pdf(
    rect: RectEscena, origen_x: float, origen_y: float, escala: float
) -> RectanguloPt:
    """Inversa de `rect_pdf_a_escena`: de coordenadas de escena a puntos PDF.

    Usada al confirmar la colocación de una firma para saber dónde estamparla.
    """
    return RectanguloPt(
        x0=(rect.x - origen_x) / escala,
        y0=(rect.y - origen_y) / escala,
        x1=(rect.x + rect.ancho - origen_x) / escala,
        y1=(rect.y + rect.alto - origen_y) / escala,
    )
