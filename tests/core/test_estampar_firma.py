"""Tests del caso de uso EstamparFirma con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.estampar_firma import EstamparFirma
from tests.core.fakes import FakeEstampadoService

_RECT = RectanguloPt(100, 100, 300, 180)
_PNG = b"\x89PNG\r\n\x1a\n-datos-de-firma"


def _documento(num_paginas: int = 3) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(
            Pagina(indice=i, ancho_pt=595.0, alto_pt=842.0) for i in range(num_paginas)
        ),
    )


def test_estampa_delegando_en_el_servicio() -> None:
    servicio = FakeEstampadoService()

    EstamparFirma(servicio).ejecutar(_documento(), 1, _RECT, _PNG)

    assert servicio.estampados == [("doc-1", 1, _RECT, _PNG)]


@pytest.mark.parametrize("pagina", [-1, 3, 99])
def test_pagina_fuera_de_rango(pagina: int) -> None:
    servicio = FakeEstampadoService()

    with pytest.raises(PaginaFueraDeRango):
        EstamparFirma(servicio).ejecutar(_documento(3), pagina, _RECT, _PNG)
    assert servicio.estampados == []


def test_png_vacio_es_invalido() -> None:
    servicio = FakeEstampadoService()

    with pytest.raises(ValueError):
        EstamparFirma(servicio).ejecutar(_documento(), 0, _RECT, b"")
    assert servicio.estampados == []
