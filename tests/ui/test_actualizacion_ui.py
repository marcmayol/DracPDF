"""Tolerancia a fallos en la UI (Fase 10, tarea 4).

La comprobación automática nunca origina un diálogo ni un error de arranque; la
manual sí informa del resultado (al día / error / novedad). Se prueba el handler
de la ventana con QMessageBox mockeado (para no colgar en offscreen).
"""

from __future__ import annotations

import pytest

from lectorpdf.core.domain.actualizacion import (
    Manifiesto,
    ResultadoComprobacion,
    TipoResultado,
)
from lectorpdf.ui import main_window as mw
from lectorpdf.ui.main_window import MainWindow


def _capturar_mensajes(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    vistos: dict[str, list[str]] = {"warning": [], "information": []}
    monkeypatch.setattr(
        mw.QMessageBox, "warning", lambda *a, **k: vistos["warning"].append(a[2])
    )
    monkeypatch.setattr(
        mw.QMessageBox,
        "information",
        lambda *a, **k: vistos["information"].append(a[2]),
    )
    return vistos


def test_construir_ventana_no_dispara_comprobacion(qapp: object) -> None:
    # restaurar_sesion=False (por defecto en tests): no hay comprobación de
    # arranque; construir la ventana no toca la red ni lanza.
    ventana = MainWindow()
    try:
        assert ventana._ctrl_actu is not None
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_manual_error_informa_con_warning(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    vistos = _capturar_mensajes(monkeypatch)
    ventana = MainWindow()
    try:
        ventana._informar_comprobacion(
            ResultadoComprobacion(TipoResultado.ERROR, error="sin red")
        )
        assert len(vistos["warning"]) == 1
        assert vistos["information"] == []
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_manual_al_dia_informa_con_information(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    vistos = _capturar_mensajes(monkeypatch)
    ventana = MainWindow()
    try:
        ventana._informar_comprobacion(ResultadoComprobacion(TipoResultado.AL_DIA))
        assert len(vistos["information"]) == 1
        assert vistos["warning"] == []
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_manual_hay_actualizacion_guarda_manifiesto(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    _capturar_mensajes(monkeypatch)
    ventana = MainWindow()
    try:
        manifiesto = Manifiesto("9.9.9", "http://x/s.exe", "ab" * 32, "notas", 24)
        ventana._informar_comprobacion(
            ResultadoComprobacion(
                TipoResultado.HAY_ACTUALIZACION, manifiesto=manifiesto
            )
        )
        assert ventana._manifiesto_disponible is manifiesto
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)
