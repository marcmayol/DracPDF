"""El 100 % del visor es tamaño real, no 1 píxel por punto PDF.

Un punto PDF es 1/72", la pantalla ronda 96 puntos por pulgada: pintar 1 px por
punto mostraba el documento un 25 % más pequeño que Adobe y el resto de visores.
"""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget, factor_dpi
from tests.core.fakes import FakeDocumentRepository

_A4_ANCHO_PT = 595.0
_A4_ALTO_PT = 842.0


def _visor() -> tuple[ViewerWidget, Documento, FakeDocumentRepository]:
    documento = Documento(
        id="doc-1",
        ruta=Path("d.pdf"),
        paginas=tuple(
            Pagina(indice=i, ancho_pt=_A4_ANCHO_PT, alto_pt=_A4_ALTO_PT)
            for i in range(3)
        ),
    )
    imagen = ImagenRenderizada(
        ancho_px=100, alto_px=140, datos=b"\x00" * (100 * 140 * 4), escala=1.0
    )
    repo = FakeDocumentRepository(documento=documento, imagen=imagen)
    return ViewerWidget(RenderizarPagina(repo)), documento, repo


def test_el_factor_dpi_no_es_uno(qapp: object) -> None:
    """96/72 = 1,333. Si esto vuelve a valer 1, el visor se quedó en 72 DPI."""
    assert factor_dpi() > 1.3


def test_al_cien_por_cien_la_pagina_mide_su_tamano_real(qapp: object) -> None:
    visor, documento, _ = _visor()

    visor.set_documento(documento, 1.0)

    rect = visor.rect_pagina(0)
    assert rect is not None
    assert visor.escala == 1.0  # el usuario ve "100 %"
    # Un A4 al 100 % ocupa 595 pt × 96/72 ≈ 793 px, no 595.
    assert round(rect.width()) == round(_A4_ANCHO_PT * factor_dpi())
    assert round(rect.height()) == round(_A4_ALTO_PT * factor_dpi())


def test_el_render_se_pide_a_la_escala_de_pixeles(qapp: object) -> None:
    visor, documento, repo = _visor()
    visor.resize(900, 700)
    visor.show()

    visor.set_documento(documento, 1.0)

    escalas = [llamada[-1] for llamada in repo.render_llamadas]
    assert escalas, "debería haber renderizado alguna página"
    assert all(abs(e - factor_dpi()) < 0.001 for e in escalas)


def test_el_zoom_multiplica_sobre_el_tamano_real(qapp: object) -> None:
    visor, documento, _ = _visor()

    visor.set_documento(documento, 1.0)
    visor.set_escala(2.0)

    rect = visor.rect_pagina(0)
    assert rect is not None
    assert visor.escala == 2.0
    assert visor.escala_px == 2.0 * factor_dpi()
    assert round(rect.width()) == round(_A4_ANCHO_PT * 2.0 * factor_dpi())


def test_ajustar_a_ancho_devuelve_zoom_no_pixeles_por_punto(qapp: object) -> None:
    """El ajuste calcula píxeles por punto; lo que se guarda y se enseña es el
    zoom, así que hay que dividir por el factor o el % saldría inflado."""
    visor, documento, _ = _visor()
    visor.resize(900, 700)
    visor.show()
    visor.set_documento(documento, 1.0)

    zoom = visor.escala_para_ancho()
    visor.ajustar_a_ancho()

    rect = visor.rect_pagina(0)
    assert rect is not None
    assert abs(visor.escala - zoom) < 0.001
    # La página cabe a lo ancho del viewport (menos los márgenes).
    assert rect.width() <= visor.viewport().width()
