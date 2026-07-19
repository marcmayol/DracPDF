"""Tests de la conversión ImagenRenderizada -> QImage."""

from __future__ import annotations

from PySide6.QtGui import QImage, QPixmap

from lectorpdf.core.domain.modelos import ImagenRenderizada
from lectorpdf.ui.viewer.imagen import qimagen_desde, qpixmap_desde


def _imagen_2x1_roja() -> ImagenRenderizada:
    # Dos píxeles rojos opacos: R=255, G=0, B=0, A=255.
    datos = bytes([255, 0, 0, 255, 255, 0, 0, 255])
    return ImagenRenderizada(ancho_px=2, alto_px=1, datos=datos, escala=1.0)


def test_qimagen_respeta_dimensiones_formato_y_color(qapp: object) -> None:
    imagen = _imagen_2x1_roja()

    qimg = qimagen_desde(imagen)

    assert qimg.width() == 2
    assert qimg.height() == 1
    assert qimg.format() == QImage.Format.Format_RGBA8888
    color = qimg.pixelColor(0, 0)
    assert (color.red(), color.green(), color.blue(), color.alpha()) == (255, 0, 0, 255)


def test_qpixmap_desde_devuelve_pixmap_del_tamano_correcto(qapp: object) -> None:
    pixmap = qpixmap_desde(_imagen_2x1_roja())

    assert isinstance(pixmap, QPixmap)
    assert pixmap.width() == 2
    assert pixmap.height() == 1
