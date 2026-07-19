"""Tests del caso de uso VerificarFirmas con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.firma_digital import EstadoFirma, ResultadoVerificacion
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.verificar_firmas import VerificarFirmas
from tests.core.fakes import FakeSignatureService


def _documento() -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=(Pagina(indice=0, ancho_pt=400.0, alto_pt=600.0),),
    )


def test_devuelve_los_resultados_del_servicio() -> None:
    resultado = ResultadoVerificacion(
        firmante="Ana",
        estado=EstadoFirma.VALIDA,
        cubre_todo_el_documento=True,
        sellada_en_tiempo=False,
        motivo="ok",
    )
    servicio = FakeSignatureService(resultados=(resultado,))

    salida = VerificarFirmas(servicio).ejecutar(_documento())

    assert salida == (resultado,)
    assert servicio.verificaciones == ["doc-1"]
