"""Tests del ViewerWidget usando un fake del repositorio (sin PyMuPDF)."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.viewer.viewer_widget import MARGEN_PX, ViewerWidget
from tests.core.fakes import FakeDocumentRepository


def _documento(num_paginas: int = 3) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(
            Pagina(indice=i, ancho_pt=100.0, alto_pt=200.0) for i in range(num_paginas)
        ),
    )


def _viewer(documento: Documento) -> ViewerWidget:
    imagen = ImagenRenderizada(
        ancho_px=100, alto_px=200, datos=b"\x00" * (100 * 200 * 4), escala=1.0
    )
    repo = FakeDocumentRepository(documento=documento, imagen=imagen)
    return ViewerWidget(RenderizarPagina(repo))


def test_set_documento_crea_un_fondo_por_pagina(qapp: object) -> None:
    documento = _documento(num_paginas=4)
    visor = _viewer(documento)

    visor.set_documento(documento)

    assert len(visor._fondos) == 4
    assert set(visor._geometria) == {0, 1, 2, 3}


def test_geometria_apila_verticalmente_con_margen(qapp: object) -> None:
    documento = _documento(num_paginas=2)
    visor = _viewer(documento)

    visor.set_documento(documento, escala=1.0)

    rect0 = visor._geometria[0]
    rect1 = visor._geometria[1]
    assert rect0.height() == 200.0
    # La segunda página empieza tras la primera más el margen.
    assert rect1.top() == MARGEN_PX + 200.0 + MARGEN_PX


def test_render_voraz_muestra_todas_las_paginas(qapp: object) -> None:
    documento = _documento(num_paginas=3)
    visor = _viewer(documento)

    visor.set_documento(documento)

    assert set(visor._pixmaps) == {0, 1, 2}


def test_escala_afecta_al_tamano_de_las_paginas(qapp: object) -> None:
    documento = _documento(num_paginas=1)
    visor = _viewer(documento)

    visor.set_documento(documento, escala=2.0)

    assert visor._geometria[0].width() == 200.0
    assert visor._geometria[0].height() == 400.0
