"""Tests de FormLayer: colocación de proxies de campo sobre el visor."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.formularios import (
    CampoFormulario,
    RectanguloPt,
    TipoCampo,
)
from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.forms.form_layer import FormLayer
from lectorpdf.ui.viewer.viewer_widget import MARGEN_PX, ViewerWidget
from tests.core.fakes import FakeDocumentRepository


def _documento(num_paginas: int = 3) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(
            Pagina(indice=i, ancho_pt=400.0, alto_pt=600.0) for i in range(num_paginas)
        ),
    )


def _visor(documento: Documento) -> ViewerWidget:
    imagen = ImagenRenderizada(
        ancho_px=400, alto_px=600, datos=b"\x00" * (400 * 600 * 4), escala=1.0
    )
    repo = FakeDocumentRepository(documento=documento, imagen=imagen)
    return ViewerWidget(RenderizarPagina(repo))


def _campo(campo_id: str, pagina: int) -> CampoFormulario:
    return CampoFormulario(
        id=campo_id,
        nombre="nombre",
        tipo=TipoCampo.TEXTO,
        pagina=pagina,
        rect_pt=RectanguloPt(50, 60, 250, 80),
        valor="",
    )


def test_crea_proxy_para_campo_de_pagina_visible(qapp: object) -> None:
    documento = _documento()
    visor = _visor(documento)
    capa = FormLayer(visor)
    visor.set_documento(documento)

    capa.set_campos((_campo("0:0", pagina=0),))

    assert "0:0" in capa.proxies()


def test_proxy_alineado_con_la_transformacion(qapp: object) -> None:
    documento = _documento()
    visor = _visor(documento)
    capa = FormLayer(visor)
    visor.set_documento(documento, escala=1.0)

    capa.set_campos((_campo("0:0", pagina=0),))
    rect = capa.proxies()["0:0"].sceneBoundingRect()

    # Página 0: origen en (x=?, y=MARGEN). El campo está en (50,60)+origen.
    origen = visor.rect_pagina(0)
    assert rect.left() == origen.left() + 50.0
    assert rect.top() == MARGEN_PX + 60.0
    assert rect.width() == 200.0
    assert rect.height() == 20.0


def test_proxy_se_realinea_tras_zoom(qapp: object) -> None:
    documento = _documento()
    visor = _visor(documento)
    capa = FormLayer(visor)
    visor.set_documento(documento, escala=1.0)
    capa.set_campos((_campo("0:0", pagina=0),))

    visor.set_escala(2.0)
    rect = capa.proxies()["0:0"].sceneBoundingRect()

    origen = visor.rect_pagina(0)
    # A escala 2.0 el campo dobla posición relativa y tamaño.
    assert rect.left() == origen.left() + 100.0
    assert rect.width() == 400.0
    assert rect.height() == 40.0


def test_no_crea_proxies_de_paginas_no_visibles(qapp: object) -> None:
    documento = _documento(num_paginas=50)
    visor = _visor(documento)
    visor.resize(400, 300)
    capa = FormLayer(visor)
    visor.set_documento(documento)

    # Un campo en una página muy lejana no debe tener proxy.
    capa.set_campos((_campo("40:0", pagina=40),))

    assert "40:0" not in capa.proxies()
