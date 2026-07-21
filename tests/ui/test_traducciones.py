"""Test de carga de las traducciones estándar de Qt en español."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from lectorpdf.ui.app import cargar_traducciones


def test_carga_traducciones_es_traduce_botones_estandar(qapp: object) -> None:
    app = QApplication.instance()
    assert isinstance(app, QApplication)

    traductores = cargar_traducciones(app)
    try:
        assert traductores, "no se cargó qtbase_es (¿faltan los .qm de PySide6?)"
        assert app.translate("QPlatformTheme", "Cancel") == "Cancelar"
        assert app.translate("QPlatformTheme", "Close") == "Cerrar"
    finally:
        for traductor in traductores:
            app.removeTranslator(traductor)
