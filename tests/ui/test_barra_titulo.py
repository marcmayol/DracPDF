"""Tests del gestor de barra de título (DWM modo oscuro)."""

from __future__ import annotations

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QWidget

from lectorpdf.ui.theme.barra_titulo import GestorBarraTitulo, aplicar_modo_oscuro


def test_aplicar_modo_oscuro_es_seguro(qapp: object) -> None:
    # No debe lanzar (no-op fuera de Windows; DWM ignora errores en Windows).
    widget = QWidget()
    aplicar_modo_oscuro(widget, True)
    aplicar_modo_oscuro(widget, False)


def test_gestor_actualiza_su_flag(qapp: object) -> None:
    gestor = GestorBarraTitulo(oscuro=True)
    assert gestor._oscuro is True
    gestor.set_oscuro(False)
    assert gestor._oscuro is False


def test_gestor_ignora_eventos_que_no_son_show(qapp: object) -> None:
    gestor = GestorBarraTitulo(oscuro=True)
    # No debe lanzar con un widget no-ventana ni con otros eventos.
    hijo = QWidget()
    assert gestor.eventFilter(hijo, QEvent(QEvent.Type.Show)) is False
