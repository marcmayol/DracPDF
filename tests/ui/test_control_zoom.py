"""Tests del control de zoom editable de la toolbar."""

from __future__ import annotations

from lectorpdf.ui.controles.control_zoom import ControlZoom


def test_set_zoom_muestra_porcentaje(qapp: object) -> None:
    control = ControlZoom()
    control.set_zoom(0.92)  # 92 %

    assert control._campo.text() == "92"


def test_set_zoom_redondea(qapp: object) -> None:
    control = ControlZoom()
    control.set_zoom(1.256)

    assert control._campo.text() == "126"


def test_editar_el_campo_emite_factor(qapp: object) -> None:
    control = ControlZoom()
    pedidos: list[float] = []
    control.zoom_pedido.connect(pedidos.append)

    control._campo.setText("150")
    control._campo.editingFinished.emit()

    assert pedidos == [1.5]


def test_editar_fuera_de_rango_se_acota(qapp: object) -> None:
    control = ControlZoom()
    pedidos: list[float] = []
    control.zoom_pedido.connect(pedidos.append)

    control._campo.setText("5000")
    control._campo.editingFinished.emit()

    assert pedidos == [8.0]  # acotado a 800 %


def test_botones_emiten_acercar_alejar(qapp: object) -> None:
    control = ControlZoom()
    eventos: list[str] = []
    control.acercar.connect(lambda: eventos.append("+"))
    control.alejar.connect(lambda: eventos.append("-"))

    control._acercar.click()
    control._alejar.click()

    assert eventos == ["+", "-"]
