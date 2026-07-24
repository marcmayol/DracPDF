"""Tests del controlador de actualizaciones: decisiones automática vs manual y
el ajuste, sin red (se prueba la lógica _procesar y las preferencias)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from lectorpdf.core.domain.actualizacion import (
    Manifiesto,
    ResultadoComprobacion,
    TipoResultado,
)
from lectorpdf.core.use_cases.comprobar_actualizacion import ComprobarActualizacion
from lectorpdf.ui.actualizaciones.controlador_actualizacion import (
    ControladorActualizacion,
)


class _FakeActu:
    def descargar_manifiesto(
        self, etag: str | None = None
    ) -> tuple[Manifiesto | None, str | None]:
        return None, etag

    def descargar_instalador(self, url: str, destino: Path) -> Path:
        return destino

    def sha256(self, ruta: Path) -> str:
        return ""

    def lanzar_instalador(self, ruta: Path) -> None:
        pass


def _manifiesto() -> Manifiesto:
    return Manifiesto("0.9.0", "http://x/s.exe", "ab" * 32, "Novedades", 24)


def _controlador(tmp_path: Path) -> ControladorActualizacion:
    prefs = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    caso = ComprobarActualizacion(_FakeActu())
    return ControladorActualizacion(caso, "0.2.1", prefs)


def _capturar(senal: object) -> list[object]:
    recibido: list[object] = []
    senal.connect(lambda x: recibido.append(x))  # type: ignore[attr-defined]
    return recibido


def test_automatico_activado_por_defecto(qapp: object, tmp_path: Path) -> None:
    assert _controlador(tmp_path).automatico_activado() is True


def test_set_automatico_persiste_y_para_timer(qapp: object, tmp_path: Path) -> None:
    ctrl = _controlador(tmp_path)
    ctrl.set_automatico(False)
    assert ctrl.automatico_activado() is False


def test_hay_actualizacion_automatica_emite_banda_no_informa(
    qapp: object, tmp_path: Path
) -> None:
    ctrl = _controlador(tmp_path)
    banda = _capturar(ctrl.actualizacion_disponible)
    informa = _capturar(ctrl.comprobacion_terminada)
    res = ResultadoComprobacion(TipoResultado.HAY_ACTUALIZACION, manifiesto=_manifiesto())
    ctrl._procesar(res, manual=False)
    assert len(banda) == 1
    assert informa == []  # automática no informa


def test_hay_actualizacion_manual_emite_ambas(qapp: object, tmp_path: Path) -> None:
    ctrl = _controlador(tmp_path)
    banda = _capturar(ctrl.actualizacion_disponible)
    informa = _capturar(ctrl.comprobacion_terminada)
    res = ResultadoComprobacion(TipoResultado.HAY_ACTUALIZACION, manifiesto=_manifiesto())
    ctrl._procesar(res, manual=True)
    assert len(banda) == 1 and len(informa) == 1


def test_al_dia_manual_informa_automatica_calla(
    qapp: object, tmp_path: Path
) -> None:
    ctrl = _controlador(tmp_path)
    informa = _capturar(ctrl.comprobacion_terminada)
    al_dia = ResultadoComprobacion(TipoResultado.AL_DIA, manifiesto=_manifiesto())
    ctrl._procesar(al_dia, manual=False)
    assert informa == []
    ctrl._procesar(al_dia, manual=True)
    assert len(informa) == 1


def test_error_automatico_es_silencioso(qapp: object, tmp_path: Path) -> None:
    ctrl = _controlador(tmp_path)
    banda = _capturar(ctrl.actualizacion_disponible)
    informa = _capturar(ctrl.comprobacion_terminada)
    err = ResultadoComprobacion(TipoResultado.ERROR, error="sin red")
    ctrl._procesar(err, manual=False)
    assert banda == [] and informa == []  # silencio total


def test_error_manual_informa(qapp: object, tmp_path: Path) -> None:
    ctrl = _controlador(tmp_path)
    informa = _capturar(ctrl.comprobacion_terminada)
    err = ResultadoComprobacion(TipoResultado.ERROR, error="sin red")
    ctrl._procesar(err, manual=True)
    assert len(informa) == 1


def test_etag_se_persiste(qapp: object, tmp_path: Path) -> None:
    ini = tmp_path / "s.ini"
    prefs = QSettings(str(ini), QSettings.Format.IniFormat)
    ctrl = ControladorActualizacion(ComprobarActualizacion(_FakeActu()), "0.2.1", prefs)
    res = ResultadoComprobacion(
        TipoResultado.AL_DIA, manifiesto=_manifiesto(), etag='"abc"'
    )
    ctrl._procesar(res, manual=False)
    assert prefs.value("actualizaciones/etag") == '"abc"'


def test_iniciar_con_automatico_desactivado_no_programa(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctrl = _controlador(tmp_path)
    ctrl.set_automatico(False)
    llamado: list[bool] = []
    monkeypatch.setattr(ctrl, "comprobar", lambda manual: llamado.append(manual))
    ctrl.iniciar()
    # No hay comprobación de arranque programada si el ajuste está desactivado.
    assert llamado == []
