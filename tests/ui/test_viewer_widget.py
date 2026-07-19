"""Tests del ViewerWidget usando un fake del repositorio (sin PyMuPDF)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF

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


def _repo(documento: Documento) -> FakeDocumentRepository:
    imagen = ImagenRenderizada(
        ancho_px=100, alto_px=200, datos=b"\x00" * (100 * 200 * 4), escala=1.0
    )
    return FakeDocumentRepository(documento=documento, imagen=imagen)


def _renders_de_pagina(repo: FakeDocumentRepository, indice: int) -> int:
    return sum(1 for (_, i, _) in repo.render_llamadas if i == indice)


# -- Construcción de la escena ---------------------------------------------


def test_set_documento_crea_un_fondo_por_pagina(qapp: object) -> None:
    documento = _documento(num_paginas=4)
    visor = ViewerWidget(RenderizarPagina(_repo(documento)))

    visor.set_documento(documento)

    assert len(visor._fondos) == 4
    assert set(visor._geometria) == {0, 1, 2, 3}


def test_geometria_apila_verticalmente_con_margen(qapp: object) -> None:
    documento = _documento(num_paginas=2)
    visor = ViewerWidget(RenderizarPagina(_repo(documento)))

    visor.set_documento(documento, escala=1.0)

    assert visor._geometria[0].height() == 200.0
    assert visor._geometria[1].top() == MARGEN_PX + 200.0 + MARGEN_PX


def test_escala_afecta_al_tamano_de_las_paginas(qapp: object) -> None:
    documento = _documento(num_paginas=1)
    visor = ViewerWidget(RenderizarPagina(_repo(documento)))

    visor.set_documento(documento, escala=2.0)

    assert visor._geometria[0].width() == 200.0
    assert visor._geometria[0].height() == 400.0


# -- Selección de páginas visibles (± 1) -----------------------------------


def test_indices_en_rect_incluye_visibles_y_vecinos(qapp: object) -> None:
    documento = _documento(num_paginas=10)
    visor = ViewerWidget(RenderizarPagina(_repo(documento)))
    visor.set_documento(documento)

    # Rectángulo que cubre solo la página 5.
    rect_pag5 = visor._geometria[5]
    deseados = visor._indices_en_rect(rect_pag5)

    # La 5 más sus vecinas 4 y 6.
    assert deseados == {4, 5, 6}


def test_indices_en_rect_no_sale_de_los_limites(qapp: object) -> None:
    documento = _documento(num_paginas=3)
    visor = ViewerWidget(RenderizarPagina(_repo(documento)))
    visor.set_documento(documento)

    deseados = visor._indices_en_rect(visor._geometria[0])

    assert deseados == {0, 1}  # no incluye -1


def test_hueco_entre_paginas_elige_la_mas_cercana(qapp: object) -> None:
    documento = _documento(num_paginas=5)
    visor = ViewerWidget(RenderizarPagina(_repo(documento)))
    visor.set_documento(documento)

    # Franja vacía muy por debajo de todas las páginas.
    rect_vacio = QRectF(0, 100_000, 10, 10)
    deseados = visor._indices_en_rect(rect_vacio)

    # La más cercana es la última; se muestran ella y su vecina.
    assert deseados == {3, 4}


# -- Render perezoso y caché -----------------------------------------------


def test_no_renderiza_todas_las_paginas_de_un_documento_grande(qapp: object) -> None:
    documento = _documento(num_paginas=100)
    repo = _repo(documento)
    visor = ViewerWidget(RenderizarPagina(repo))
    visor.resize(400, 300)

    visor.set_documento(documento)

    assert len(visor.indices_mostrados()) < 100
    # Solo se ha renderizado lo mostrado, no las 100 páginas.
    assert len(repo.render_llamadas) == len(visor.indices_mostrados())


def test_volver_a_mostrar_una_pagina_usa_la_cache(qapp: object) -> None:
    documento = _documento(num_paginas=10)
    repo = _repo(documento)
    visor = ViewerWidget(RenderizarPagina(repo))
    visor.set_documento(documento)

    visor._mostrar_pagina(0)
    renders_iniciales = _renders_de_pagina(repo, 0)
    assert renders_iniciales == 1

    # Se oculta y se vuelve a pedir: debe salir de la caché, sin re-renderizar.
    visor._scene.removeItem(visor._pixmaps.pop(0))
    visor._mostrar_pagina(0)

    assert _renders_de_pagina(repo, 0) == 1
