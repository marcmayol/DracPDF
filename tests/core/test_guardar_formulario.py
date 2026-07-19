"""Tests del caso de uso GuardarFormulario con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.formularios import (
    CampoFormulario,
    RectanguloPt,
    TipoCampo,
)
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.guardar_formulario import GuardarFormulario
from lectorpdf.core.use_cases.rellenar_campo import RellenarCampo
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
        rect_pt=RectanguloPt(0, 0, 100, 20),
        valor="",
    )


def test_guardar_incremental_delega_con_destino_none() -> None:
    servicio = FakeFormService(campos=(_campo(),))

    GuardarFormulario(servicio).ejecutar(_documento())

    assert servicio.guardados == [("doc-1", None)]


def test_guardar_con_destino_explicito() -> None:
    servicio = FakeFormService(campos=(_campo(),))
    destino = Path("copia.pdf")

    GuardarFormulario(servicio).ejecutar(_documento(), destino)

    assert servicio.guardados == [("doc-1", destino)]


def test_hay_cambios_refleja_estado_sucio() -> None:
    campo = _campo()
    servicio = FakeFormService(campos=(campo,))
    documento = _documento()
    guardar = GuardarFormulario(servicio)

    assert guardar.hay_cambios_sin_guardar(documento) is False

    RellenarCampo(servicio).ejecutar(documento, campo, "Marc")
    assert guardar.hay_cambios_sin_guardar(documento) is True

    guardar.ejecutar(documento)
    assert guardar.hay_cambios_sin_guardar(documento) is False
