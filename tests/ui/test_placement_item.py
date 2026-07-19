"""Tests del item de colocación de firma (redimensionado con proporción)."""

from __future__ import annotations

import fitz
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPixmap

from lectorpdf.ui.signature.placement_item import SignaturePlacementItem


def _pixmap() -> QPixmap:
    png = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 40), False).tobytes("png")
    pixmap = QPixmap()
    pixmap.loadFromData(png)
    return pixmap


def test_redimensionar_conserva_la_proporcion(qapp: object) -> None:
    item = SignaturePlacementItem(_pixmap(), ancho=100.0, alto=40.0)  # prop 0.4

    item.redimensionar_desde_ancho(200.0)

    assert item.tamano() == (200.0, 80.0)


def test_redimensionar_respeta_ancho_minimo(qapp: object) -> None:
    item = SignaturePlacementItem(_pixmap(), ancho=100.0, alto=40.0)

    item.redimensionar_desde_ancho(1.0)  # por debajo del mínimo

    ancho, alto = item.tamano()
    assert ancho >= 24.0
    assert alto == ancho * 0.4  # sigue proporcional


def test_mover_actualiza_el_rect_en_escena(qapp: object) -> None:
    item = SignaturePlacementItem(_pixmap(), ancho=100.0, alto=40.0)

    item.setPos(QPointF(30, 50))

    rect = item.rect_en_escena()
    assert (rect.left(), rect.top()) == (30.0, 50.0)
    assert (rect.width(), rect.height()) == (100.0, 40.0)
