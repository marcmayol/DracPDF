"""Tests de los casos de uso de tablas con un fake del puerto."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.errores import ErrorDominio
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.domain.tablas import (
    EstrategiaTablas,
    FormatoTabla,
    TablaDetectada,
)
from lectorpdf.core.use_cases.convertir_tablas import ConvertirTablas, DetectarTablas


class FakeServicioTablas:
    def __init__(self, detectadas=(), rutas=()) -> None:  # type: ignore[no-untyped-def]
        self._detectadas = tuple(detectadas)
        self._rutas = list(rutas)
        self.estrategias: list[EstrategiaTablas] = []

    def detectar_tablas(self, documento_id, estrategia=EstrategiaTablas.LINEAS, progreso=None):  # type: ignore[no-untyped-def]
        self.estrategias.append(estrategia)
        return self._detectadas

    def exportar_tablas(  # type: ignore[no-untyped-def]
        self,
        documento_id,
        directorio,
        formato,
        estrategia=EstrategiaTablas.LINEAS,
        progreso=None,
    ):
        self.estrategias.append(estrategia)
        return list(self._rutas)


def _documento() -> Documento:
    return Documento(id="doc-1", ruta=Path("d.pdf"), paginas=(Pagina(0, 400.0, 600.0),))


def test_detectar_pasa_la_estrategia_elegida() -> None:
    servicio = FakeServicioTablas(detectadas=(TablaDetectada(0, 0, 3, 2),))

    detectadas = DetectarTablas(servicio).ejecutar(_documento(), EstrategiaTablas.TEXTO)

    assert len(detectadas) == 1
    assert servicio.estrategias == [EstrategiaTablas.TEXTO]


def test_convertir_devuelve_las_rutas_escritas(tmp_path: Path) -> None:
    esperadas = [tmp_path / "d_p1_t1.csv"]
    servicio = FakeServicioTablas(rutas=esperadas)

    rutas = ConvertirTablas(servicio).ejecutar(
        _documento(), tmp_path, FormatoTabla.CSV
    )

    assert rutas == esperadas


def test_convertir_sin_tablas_avisa_en_vez_de_dejar_ficheros_vacios(
    tmp_path: Path,
) -> None:
    servicio = FakeServicioTablas(rutas=())

    with pytest.raises(ErrorDominio, match="ninguna tabla"):
        ConvertirTablas(servicio).ejecutar(_documento(), tmp_path, FormatoTabla.XLSX)


def test_el_nombre_de_la_tabla_identifica_pagina_y_orden() -> None:
    assert TablaDetectada(0, 0, 1, 1).nombre == "p1_t1"
    assert TablaDetectada(4, 2, 1, 1).nombre == "p5_t3"
