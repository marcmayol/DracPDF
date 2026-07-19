"""Conversión de la imagen de dominio (RGBA) a tipos de Qt."""

from __future__ import annotations

from PySide6.QtGui import QImage, QPixmap

from lectorpdf.core.domain.modelos import ImagenRenderizada


def qimagen_desde(imagen: ImagenRenderizada) -> QImage:
    """Construye un QImage a partir de los bytes RGBA de `ImagenRenderizada`.

    Se copia el buffer para que el QImage sea dueño de sus datos y no dependa
    del ciclo de vida de `imagen.datos`.
    """
    qimg = QImage(
        imagen.datos,
        imagen.ancho_px,
        imagen.alto_px,
        imagen.ancho_px * 4,
        QImage.Format.Format_RGBA8888,
    )
    return qimg.copy()


def qpixmap_desde(imagen: ImagenRenderizada) -> QPixmap:
    return QPixmap.fromImage(qimagen_desde(imagen))
