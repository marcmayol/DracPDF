"""Tests de exportación a PNG transparente del SignatureCanvas."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QImage, QMouseEvent

from lectorpdf.ui.signature.signature_canvas import SignatureCanvas


def _dibujar_trazo(canvas: SignatureCanvas) -> None:
    canvas.mousePressEvent(
        QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(20, 60),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    for x, y in [(60, 20), (100, 70), (140, 25)]:
        canvas.mouseMoveEvent(
            QMouseEvent(
                QEvent.Type.MouseMove,
                QPointF(x, y),
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
        )


def test_exportar_lienzo_vacio_lanza_error(qapp: object) -> None:
    with pytest.raises(ValueError):
        SignatureCanvas().exportar_png()


def test_exportar_produce_png_con_alfa(qapp: object) -> None:
    canvas = SignatureCanvas()
    _dibujar_trazo(canvas)

    datos = canvas.exportar_png()

    assert datos[:4] == b"\x89PNG"
    imagen = QImage.fromData(datos, "PNG")
    assert not imagen.isNull()
    assert imagen.hasAlphaChannel()
    # La esquina superior izquierda debe ser transparente.
    assert imagen.pixelColor(0, 0).alpha() == 0
    # Debe haber al menos un píxel de tinta opaco.
    opacos = any(
        imagen.pixelColor(x, y).alpha() > 0
        for x in range(imagen.width())
        for y in range(imagen.height())
    )
    assert opacos


def test_exportar_recorta_a_los_trazos(qapp: object) -> None:
    canvas = SignatureCanvas()
    canvas.setMinimumSize(800, 600)
    _dibujar_trazo(canvas)

    imagen = QImage.fromData(canvas.exportar_png(), "PNG")

    # El PNG se ajusta al trazo (~120x50 + márgenes), no al tamaño del widget.
    assert imagen.width() < 300
    assert imagen.height() < 200
