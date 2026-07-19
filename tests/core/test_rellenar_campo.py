"""Tests del caso de uso RellenarCampo con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.errores import CampoSoloLectura, ValorDeCampoInvalido
from lectorpdf.core.domain.formularios import (
    CampoFormulario,
    RectanguloPt,
    TipoCampo,
)
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.rellenar_campo import RellenarCampo
from tests.core.fakes import FakeFormService

_RECT = RectanguloPt(0, 0, 100, 20)


def _documento() -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=(Pagina(indice=0, ancho_pt=400.0, alto_pt=600.0),),
    )


def _campo(tipo: TipoCampo, **kw: object) -> CampoFormulario:
    base: dict[str, object] = dict(
        id="0:0", nombre="c", tipo=tipo, pagina=0, rect_pt=_RECT, valor=""
    )
    base.update(kw)
    return CampoFormulario(**base)  # type: ignore[arg-type]


def test_escribe_texto_delegando_en_el_servicio() -> None:
    campo = _campo(TipoCampo.TEXTO)
    servicio = FakeFormService(campos=(campo,))

    RellenarCampo(servicio).ejecutar(_documento(), campo, "Marc")

    assert servicio.escrituras == [("doc-1", "0:0", "Marc")]


def test_campo_solo_lectura_no_se_escribe() -> None:
    campo = _campo(TipoCampo.TEXTO, solo_lectura=True)
    servicio = FakeFormService(campos=(campo,))

    with pytest.raises(CampoSoloLectura):
        RellenarCampo(servicio).ejecutar(_documento(), campo, "x")
    assert servicio.escrituras == []


def test_valor_fuera_de_opciones_en_combo_es_invalido() -> None:
    campo = _campo(TipoCampo.COMBO, opciones=("ES", "FR"))
    servicio = FakeFormService(campos=(campo,))

    with pytest.raises(ValorDeCampoInvalido):
        RellenarCampo(servicio).ejecutar(_documento(), campo, "XX")
    assert servicio.escrituras == []


def test_radio_solo_acepta_una_opcion_valida() -> None:
    campo = _campo(TipoCampo.RADIO, opciones=("Yes",), estado_activado="Yes")
    servicio = FakeFormService(campos=(campo,))

    RellenarCampo(servicio).ejecutar(_documento(), campo, "Yes")
    with pytest.raises(ValorDeCampoInvalido):
        RellenarCampo(servicio).ejecutar(_documento(), campo, "No")

    assert servicio.escrituras == [("doc-1", "0:0", "Yes")]


def test_casilla_acepta_on_y_off() -> None:
    campo = _campo(TipoCampo.CASILLA, opciones=("Yes",), estado_activado="Yes")
    servicio = FakeFormService(campos=(campo,))

    RellenarCampo(servicio).ejecutar(_documento(), campo, "Yes")
    RellenarCampo(servicio).ejecutar(_documento(), campo, "Off")

    assert servicio.escrituras[-2:] == [
        ("doc-1", "0:0", "Yes"),
        ("doc-1", "0:0", "Off"),
    ]
