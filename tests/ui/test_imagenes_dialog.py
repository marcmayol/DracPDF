"""Tests del diálogo de imágenes → PDF (orden, ajuste y lista vacía)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialogButtonBox

from lectorpdf.core.domain.conversion import AjusteImagen
from lectorpdf.ui.conversion.imagenes_dialog import ConversionImagenesDialog


def _rutas() -> list[Path]:
    return [Path("a.png"), Path("b.png"), Path("c.png")]


def test_conserva_el_orden_recibido(qapp: object) -> None:
    dialogo = ConversionImagenesDialog(_rutas())

    assert dialogo.rutas() == _rutas()
    assert dialogo.ajuste() is AjusteImagen.TAMANO_IMAGEN  # por defecto


def test_subir_y_bajar_reordenan_las_paginas(qapp: object) -> None:
    dialogo = ConversionImagenesDialog(_rutas())

    dialogo._lista.setCurrentRow(2)
    dialogo._mover(-1)  # c sube al medio

    assert [r.name for r in dialogo.rutas()] == ["a.png", "c.png", "b.png"]

    dialogo._lista.setCurrentRow(0)
    dialogo._mover(-1)  # la primera no puede subir más

    assert [r.name for r in dialogo.rutas()] == ["a.png", "c.png", "b.png"]


def test_quitar_todas_deshabilita_aceptar(qapp: object) -> None:
    dialogo = ConversionImagenesDialog(_rutas())
    boton = dialogo._botones.button(QDialogButtonBox.StandardButton.Ok)

    assert boton is not None and boton.isEnabled()

    dialogo._lista.selectAll()
    dialogo._quitar()

    assert dialogo.rutas() == []
    assert not boton.isEnabled()  # no se convierte un PDF de cero páginas


def test_tamano_y_margen_solo_con_pagina_fija(qapp: object) -> None:
    dialogo = ConversionImagenesDialog(_rutas())

    assert not dialogo._tamano.isEnabled()  # con "tamaño de su imagen" no pintan nada

    dialogo._ajuste.setCurrentIndex(1)  # página fija

    assert dialogo.ajuste() is AjusteImagen.PAGINA_FIJA
    assert dialogo._tamano.isEnabled()
    assert dialogo._margen.isEnabled()
    assert dialogo.config().margen_mm == 20.0
