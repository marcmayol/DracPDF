"""Tests del caso de uso ComprobarActualizacion con un fake del puerto."""

from __future__ import annotations

import json
from pathlib import Path

from lectorpdf.core.domain.actualizacion import Manifiesto, TipoResultado
from lectorpdf.core.use_cases.comprobar_actualizacion import ComprobarActualizacion


class FakeActualizador:
    """Doble del puerto: devuelve un manifiesto fijo, un 304, o lanza."""

    def __init__(
        self,
        manifiesto: Manifiesto | None = None,
        etag: str | None = "nuevo-etag",
        excepcion: Exception | None = None,
        es_304: bool = False,
    ) -> None:
        self._manifiesto = manifiesto
        self._etag = etag
        self._excepcion = excepcion
        self._es_304 = es_304

    def descargar_manifiesto(
        self, etag: str | None = None
    ) -> tuple[Manifiesto | None, str | None]:
        if self._excepcion is not None:
            raise self._excepcion
        if self._es_304:
            return None, etag
        return self._manifiesto, self._etag

    def descargar_instalador(self, url: str, destino: Path) -> Path:  # pragma: no cover
        return destino

    def sha256(self, ruta: Path) -> str:  # pragma: no cover
        return ""

    def lanzar_instalador(self, ruta: Path) -> None:  # pragma: no cover
        pass


def _manifiesto(version: str) -> Manifiesto:
    return Manifiesto(
        version=version,
        url="https://example.com/DracPDF-setup.exe",
        sha256="00" * 32,
        notas="Notas de la versión",
        check_horas=24,
    )


def test_version_mayor_reporta_actualizacion_con_notas() -> None:
    caso = ComprobarActualizacion(FakeActualizador(_manifiesto("0.3.0")))
    res = caso.ejecutar("0.2.1")
    assert res.tipo is TipoResultado.HAY_ACTUALIZACION
    assert res.manifiesto is not None
    assert res.manifiesto.version == "0.3.0"
    assert res.manifiesto.notas == "Notas de la versión"
    assert res.etag == "nuevo-etag"


def test_version_igual_es_al_dia() -> None:
    caso = ComprobarActualizacion(FakeActualizador(_manifiesto("0.2.1")))
    assert caso.ejecutar("0.2.1").tipo is TipoResultado.AL_DIA


def test_version_menor_nunca_ofrece_bajar() -> None:
    caso = ComprobarActualizacion(FakeActualizador(_manifiesto("0.1.0")))
    assert caso.ejecutar("0.2.1").tipo is TipoResultado.AL_DIA


def test_comparacion_es_semantica_no_por_strings() -> None:
    # "0.10.0" > "0.9.0" semánticamente, aunque como string sea "menor".
    caso = ComprobarActualizacion(FakeActualizador(_manifiesto("0.10.0")))
    assert caso.ejecutar("0.9.0").tipo is TipoResultado.HAY_ACTUALIZACION


def test_304_es_sin_cambios() -> None:
    caso = ComprobarActualizacion(FakeActualizador(es_304=True))
    res = caso.ejecutar("0.2.1", etag="viejo")
    assert res.tipo is TipoResultado.SIN_CAMBIOS_ETAG
    assert res.etag == "viejo"


def test_excepcion_de_red_se_convierte_en_error() -> None:
    from urllib.error import URLError

    caso = ComprobarActualizacion(FakeActualizador(excepcion=URLError("sin red")))
    res = caso.ejecutar("0.2.1")
    assert res.tipo is TipoResultado.ERROR
    assert res.error is not None and "sin red" in res.error


def test_json_malformado_se_convierte_en_error() -> None:
    exc = json.JSONDecodeError("Expecting value", "no-json", 0)
    caso = ComprobarActualizacion(FakeActualizador(excepcion=exc))
    assert caso.ejecutar("0.2.1").tipo is TipoResultado.ERROR


def test_version_del_manifiesto_invalida_es_error() -> None:
    caso = ComprobarActualizacion(FakeActualizador(_manifiesto("no-es-version")))
    assert caso.ejecutar("0.2.1").tipo is TipoResultado.ERROR


def test_el_caso_de_uso_nunca_propaga() -> None:
    # Cualquiera que sea el fallo, ejecutar() devuelve, no lanza.
    caso = ComprobarActualizacion(FakeActualizador(excepcion=RuntimeError("boom")))
    res = caso.ejecutar("0.2.1")
    assert res.tipo is TipoResultado.ERROR
