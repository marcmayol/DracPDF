"""Tests de captura del SignatureCanvas."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent

from lectorpdf.ui.signature.signature_canvas import SignatureCanvas


def _press(x: float, y: float) -> QMouseEvent:
    return QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(x, y),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )


def _move(x: float, y: float) -> QMouseEvent:
    return QMouseEvent(
        QEvent.Type.MouseMove,
        QPointF(x, y),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,  # botón mantenido
        Qt.KeyboardModifier.NoModifier,
    )


def test_canvas_recien_creado_esta_vacio(qapp: object) -> None:
    canvas = SignatureCanvas()

    assert canvas.esta_vacio() is True


def test_captura_un_trazo_con_press_y_move(qapp: object) -> None:
    canvas = SignatureCanvas()

    canvas.mousePressEvent(_press(10, 10))
    canvas.mouseMoveEvent(_move(20, 15))
    canvas.mouseMoveEvent(_move(30, 25))

    assert canvas.esta_vacio() is False
    assert canvas.trazos() == [[(10.0, 10.0), (20.0, 15.0), (30.0, 25.0)]]


def test_dos_trazos_separados(qapp: object) -> None:
    canvas = SignatureCanvas()

    canvas.mousePressEvent(_press(0, 0))
    canvas.mouseMoveEvent(_move(5, 5))
    canvas.mousePressEvent(_press(50, 50))
    canvas.mouseMoveEvent(_move(55, 55))

    assert canvas.trazos() == [[(0.0, 0.0), (5.0, 5.0)], [(50.0, 50.0), (55.0, 55.0)]]


def test_limpiar_vacia_el_canvas(qapp: object) -> None:
    canvas = SignatureCanvas()
    canvas.mousePressEvent(_press(1, 1))
    canvas.mouseMoveEvent(_move(2, 2))

    canvas.limpiar()

    assert canvas.esta_vacio() is True
    assert canvas.trazos() == []
