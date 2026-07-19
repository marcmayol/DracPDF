"""Tests del caso de uso DividirPdf con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.errores import RangoInvalido
from lectorpdf.core.domain.herramientas import Rango
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.dividir_pdf import DividirPdf
from tests.core.fakes import FakeServicioHerramientas


def _documento(n: int = 5) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(Pagina(i, 400.0, 600.0) for i in range(n)),
    )


def test_por_paginas_genera_un_rango_por_pagina(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()

    DividirPdf(servicio).por_paginas(_documento(3), tmp_path)

    doc_id, rangos, directorio = servicio.divisiones[0]
    assert doc_id == "doc-1"
    assert rangos == [Rango(1, 1), Rango(2, 2), Rango(3, 3)]
    assert directorio == tmp_path


def test_por_rangos_delega(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()
    rangos = [Rango(1, 3), Rango(4, 5)]

    DividirPdf(servicio).por_rangos(_documento(5), rangos, tmp_path)

    assert servicio.divisiones[0][1] == rangos


def test_rango_fuera_de_limites(tmp_path: Path) -> None:
    servicio = FakeServicioHerramientas()

    with pytest.raises(RangoInvalido):
        DividirPdf(servicio).por_rangos(_documento(3), [Rango(2, 9)], tmp_path)
    assert servicio.divisiones == []
