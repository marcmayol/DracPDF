"""Tests de BarraBusqueda: emisión de señales y contador."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from lectorpdf.ui.busqueda.barra_busqueda import BarraBusqueda


def test_enter_emite_buscar_con_termino_y_case(qapp: object) -> None:
    barra = BarraBusqueda()
    barra._campo.setText("Ladon")
    barra._btn_case.setChecked(True)
    recibido: list[tuple[str, bool]] = []
    barra.buscar.connect(lambda t, c: recibido.append((t, c)))

    QTest.keyClick(barra._campo, Qt.Key.Key_Return)

    assert recibido == [("Ladon", True)]


def test_botones_emiten_siguiente_y_anterior(qapp: object) -> None:
    barra = BarraBusqueda()
    eventos: list[str] = []
    barra.siguiente.connect(lambda: eventos.append("sig"))
    barra.anterior.connect(lambda: eventos.append("ant"))

    barra._btn_next.click()
    barra._btn_prev.click()

    assert eventos == ["sig", "ant"]


def test_escape_emite_cerrada(qapp: object) -> None:
    barra = BarraBusqueda()
    cerrada: list[bool] = []
    barra.cerrada.connect(lambda: cerrada.append(True))

    QTest.keyClick(barra, Qt.Key.Key_Escape)

    assert cerrada == [True]


def test_contador_formatea_n_de_m(qapp: object) -> None:
    barra = BarraBusqueda()

    barra.mostrar_contador(2, 5)
    assert barra._contador.text() == "2 de 5"


def test_contador_sin_resultados(qapp: object) -> None:
    barra = BarraBusqueda()
    barra._campo.setText("zzz")

    barra.mostrar_contador(0, 0)
    assert barra._contador.text() == "Sin resultados"
