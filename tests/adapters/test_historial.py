"""Tests de la estructura pura HistorialEdiciones."""

from __future__ import annotations

from lectorpdf.adapters.pymupdf.historial import HistorialEdiciones


def test_deshacer_devuelve_la_ultima_edicion() -> None:
    h = HistorialEdiciones()
    h.registrar("0:0", "", "a")
    h.registrar("0:0", "a", "b")

    assert h.puede_deshacer() is True
    e = h.deshacer()
    assert e is not None and (e.antes, e.despues) == ("a", "b")
    assert h.deshacer() is not None  # la primera edición
    assert h.deshacer() is None  # nada más que deshacer


def test_rehacer_reaplica_en_orden() -> None:
    h = HistorialEdiciones()
    h.registrar("0:0", "", "a")
    h.registrar("0:0", "a", "b")
    h.deshacer()
    h.deshacer()

    assert h.rehacer() is not None
    e = h.rehacer()
    assert e is not None and e.despues == "b"
    assert h.rehacer() is None


def test_editar_tras_deshacer_descarta_el_rehacer() -> None:
    h = HistorialEdiciones()
    h.registrar("0:0", "", "a")
    h.registrar("0:0", "a", "b")
    h.deshacer()  # vuelve a "a"
    h.registrar("0:0", "a", "c")  # nueva rama

    assert h.puede_rehacer() is False
