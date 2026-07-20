"""Tests de OutlinePanel: construcción del árbol y navegación."""

from __future__ import annotations

from lectorpdf.core.domain.contenido import EntradaIndice
from lectorpdf.ui.outline.outline_panel import OutlinePanel


def _entradas() -> tuple[EntradaIndice, ...]:
    return (
        EntradaIndice(1, "Portada", 0),
        EntradaIndice(2, "Introduccion", 0),
        EntradaIndice(1, "Desarrollo", 1),
        EntradaIndice(1, "Cierre", 2),
    )


def test_construye_el_arbol_por_niveles(qapp: object) -> None:
    panel = OutlinePanel()

    tiene = panel.set_entradas(_entradas())

    assert tiene is True
    assert panel.topLevelItemCount() == 3  # Portada, Desarrollo, Cierre
    portada = panel.topLevelItem(0)
    assert portada.text(0) == "Portada"
    assert portada.childCount() == 1  # Introduccion cuelga de Portada
    assert portada.child(0).text(0) == "Introduccion"


def test_sin_entradas_devuelve_false_y_vacia(qapp: object) -> None:
    panel = OutlinePanel()
    panel.set_entradas(_entradas())

    tiene = panel.set_entradas(())

    assert tiene is False
    assert panel.topLevelItemCount() == 0


def test_pulsar_entrada_emite_su_pagina(qapp: object) -> None:
    panel = OutlinePanel()
    panel.set_entradas(_entradas())
    paginas: list[int] = []
    panel.pagina_seleccionada.connect(paginas.append)

    panel._al_pulsar(panel.topLevelItem(1), 0)  # Desarrollo -> página 1

    assert paginas == [1]


def test_no_emite_para_entrada_sin_destino(qapp: object) -> None:
    panel = OutlinePanel()
    panel.set_entradas((EntradaIndice(1, "Sin destino", -1),))
    paginas: list[int] = []
    panel.pagina_seleccionada.connect(paginas.append)

    panel._al_pulsar(panel.topLevelItem(0), 0)

    assert paginas == []
