"""Tests del caso de uso ListarCampos con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.errores import FormularioXFANoSoportado
from lectorpdf.core.domain.formularios import (
    CampoFormulario,
    RectanguloPt,
    TipoCampo,
)
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.listar_campos import ListarCampos
from tests.core.fakes import FakeFormService


def _documento() -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=(Pagina(indice=0, ancho_pt=400.0, alto_pt=600.0),),
    )


def _campo() -> CampoFormulario:
    return CampoFormulario(
        id="0:0",
        nombre="nombre",
        tipo=TipoCampo.TEXTO,
        pagina=0,
        rect_pt=RectanguloPt(50, 50, 300, 70),
        valor="",
    )


def test_lista_los_campos_del_servicio() -> None:
    campo = _campo()
    servicio = FakeFormService(campos=(campo,), es_xfa=False)

    resultado = ListarCampos(servicio).ejecutar(_documento())

    assert resultado == (campo,)


def test_documento_xfa_lanza_no_soportado() -> None:
    servicio = FakeFormService(campos=(_campo(),), es_xfa=True)

    with pytest.raises(FormularioXFANoSoportado):
        ListarCampos(servicio).ejecutar(_documento())
