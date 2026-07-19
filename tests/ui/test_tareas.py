"""Tests del envoltorio de tareas en hilo (progreso, resultado, cancelación)."""

from __future__ import annotations

from lectorpdf.core.domain.herramientas import Progreso
from lectorpdf.ui.tareas import Trabajo


def test_trabajo_emite_resultado(qapp: object) -> None:
    resultados: list[object] = []

    def funcion(progreso: Progreso) -> str:
        progreso(1, 2)
        progreso(2, 2)
        return "hecho"

    trabajo = Trabajo(funcion)
    trabajo.senales.terminado.connect(resultados.append)
    trabajo.run()  # síncrono, sin hilo, para el test

    assert resultados == ["hecho"]


def test_trabajo_emite_error(qapp: object) -> None:
    errores: list[object] = []

    def funcion(progreso: Progreso) -> None:
        raise RuntimeError("boom")

    trabajo = Trabajo(funcion)
    trabajo.senales.error.connect(errores.append)
    trabajo.run()

    assert len(errores) == 1
    assert isinstance(errores[0], RuntimeError)


def test_trabajo_cancelado_desde_el_progreso(qapp: object) -> None:
    cancelado: list[bool] = []

    def funcion(progreso: Progreso) -> None:
        progreso(1, 10)  # aquí saltará OperacionCancelada

    trabajo = Trabajo(funcion)
    trabajo.senales.cancelado.connect(lambda: cancelado.append(True))
    trabajo.cancelar()
    trabajo.run()

    assert cancelado == [True]
