"""Tolerancia a fallos en la UI (Fase 10, tarea 4).

La comprobación automática nunca origina un diálogo ni un error de arranque; la
manual sí informa del resultado (al día / error / novedad). Se prueba el handler
de la ventana con QMessageBox mockeado (para no colgar en offscreen).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from lectorpdf.core.domain.actualizacion import (
    Manifiesto,
    ResultadoComprobacion,
    TipoResultado,
)
from lectorpdf.ui import main_window as mw
from lectorpdf.ui.main_window import MainWindow


class _FakeActualizador:
    """Doble del adaptador: descarga a un fichero local y no ejecuta de verdad."""

    def __init__(self, contenido: bytes = b"instalador") -> None:
        self._contenido = contenido
        self.lanzado: Path | None = None

    def descargar_instalador(self, url: str, destino: Path) -> Path:
        destino.write_bytes(self._contenido)
        return destino

    def sha256(self, ruta: Path) -> str:
        return hashlib.sha256(ruta.read_bytes()).hexdigest()

    def lanzar_instalador(self, ruta: Path) -> None:
        self.lanzado = ruta


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
        assert not ventana._banda_actu.isHidden()  # la banda no modal aparece
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_hash_correcto_lanza_instalador_y_cierra(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    _capturar_mensajes(monkeypatch)
    contenido = b"instalador-real"
    fake = _FakeActualizador(contenido)
    sha = hashlib.sha256(contenido).hexdigest()
    ventana = MainWindow()
    try:
        ventana._actualizador = fake  # type: ignore[assignment]
        cerrado: list[bool] = []
        monkeypatch.setattr(ventana, "close", lambda: cerrado.append(True))
        manifiesto = Manifiesto("9.9.9", "http://x/s.exe", sha, "notas", 24)
        ventana._ejecutar_actualizacion(manifiesto)
        assert fake.lanzado is not None  # se lanzó el instalador
        assert cerrado == [True]  # y se cerró la app
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_hash_incorrecto_descarta_sin_ejecutar(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    vistos = _capturar_mensajes(monkeypatch)
    fake = _FakeActualizador(b"instalador-real")
    ventana = MainWindow()
    try:
        ventana._actualizador = fake  # type: ignore[assignment]
        cerrado: list[bool] = []
        monkeypatch.setattr(ventana, "close", lambda: cerrado.append(True))
        # SHA256 del manifiesto que NO coincide con lo descargado.
        manifiesto = Manifiesto("9.9.9", "http://x/s.exe", "00" * 32, "notas", 24)
        ventana._ejecutar_actualizacion(manifiesto)
        assert fake.lanzado is None  # jamás se ejecuta
        assert cerrado == []  # no se cierra la app
        assert len(vistos["warning"]) == 1  # avisa del hash incorrecto
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)
