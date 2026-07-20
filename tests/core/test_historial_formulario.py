"""Tests del caso de uso HistorialFormulario con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.formularios import CampoFormulario, RectanguloPt, TipoCampo
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.historial_formulario import HistorialFormulario
from lectorpdf.core.use_cases.rellenar_campo import RellenarCampo
from tests.core.fakes import FakeFormService


def _documento() -> Documento:
    return Documento(id="doc-1", ruta=Path("d.pdf"), paginas=(Pagina(0, 400.0, 600.0),))


def _campo() -> CampoFormulario:
    return CampoFormulario(
        id="0:0",
        nombre="n",
        tipo=TipoCampo.TEXTO,
        pagina=0,
        rect_pt=RectanguloPt(0, 0, 1, 1),
        valor="",
    )


def test_deshacer_dos_campos_restaura_en_orden() -> None:
    servicio = FakeFormService(campos=(_campo(), _campo2()))
    rellenar = RellenarCampo(servicio)
    historial = HistorialFormulario(servicio)
    doc = _documento()

    rellenar.ejecutar(doc, _campo(), "uno")
    rellenar.ejecutar(doc, _campo2(), "dos")

    # Deshacer restaura primero el segundo campo, luego el primero.
    c1 = historial.deshacer(doc)
    assert c1 is not None and (c1.campo_id, c1.valor) == ("0:1", "")
    c2 = historial.deshacer(doc)
    assert c2 is not None and (c2.campo_id, c2.valor) == ("0:0", "")
    assert historial.deshacer(doc) is None


def test_rehacer_reaplica() -> None:
    servicio = FakeFormService(campos=(_campo(),))
    rellenar = RellenarCampo(servicio)
    historial = HistorialFormulario(servicio)
    doc = _documento()

    rellenar.ejecutar(doc, _campo(), "x")
    historial.deshacer(doc)

    cambio = historial.rehacer(doc)
    assert cambio is not None and cambio.valor == "x"
    assert historial.puede_rehacer(doc) is False


def _campo2() -> CampoFormulario:
    return CampoFormulario(
        id="0:1",
        nombre="n2",
        tipo=TipoCampo.TEXTO,
        pagina=0,
        rect_pt=RectanguloPt(0, 0, 1, 1),
        valor="",
    )
