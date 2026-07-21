"""Tests del control de navegación de página de la toolbar."""

from __future__ import annotations

from lectorpdf.ui.controles.control_pagina import ControlPagina


def test_set_estado_muestra_pagina_y_total(qapp: object) -> None:
    control = ControlPagina()
    control.set_estado(2, 12)  # página 3 de 12

    assert control._campo.text() == "3"
    assert control._etiqueta_total.text() == "/ 12"
    assert control._campo.isEnabled() is True


def test_sin_documento_se_deshabilita(qapp: object) -> None:
    control = ControlPagina()
    control.set_estado(0, 0)

    assert control._campo.isEnabled() is False
    assert control._etiqueta_total.text() == "/ 0"


def test_editar_el_campo_emite_pagina_0based(qapp: object) -> None:
    control = ControlPagina()
    control.set_estado(0, 12)
    pedidas: list[int] = []
    control.pagina_pedida.connect(pedidas.append)

    control._campo.setText("5")
    control._campo.editingFinished.emit()

    assert pedidas == [4]  # página 5 (1-based) -> índice 4


def test_editar_fuera_de_rango_se_acota(qapp: object) -> None:
    control = ControlPagina()
    control.set_estado(0, 12)
    pedidas: list[int] = []
    control.pagina_pedida.connect(pedidas.append)

    control._campo.setText("999")
    control._campo.editingFinished.emit()

    assert pedidas == [11]  # acotado a la última página (índice 11)
