"""Tests del panel de miniaturas con un fake del repositorio."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.thumbnails.thumbnail_panel import ThumbnailPanel
from tests.core.fakes import FakeDocumentRepository


def _documento(num_paginas: int) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(
            Pagina(indice=i, ancho_pt=100.0, alto_pt=200.0) for i in range(num_paginas)
        ),
    )


def _panel(documento: Documento) -> tuple[ThumbnailPanel, FakeDocumentRepository]:
    imagen = ImagenRenderizada(
        ancho_px=120, alto_px=240, datos=b"\x00" * (120 * 240 * 4), escala=1.2
    )
    repo = FakeDocumentRepository(documento=documento, imagen=imagen)
    return ThumbnailPanel(RenderizarPagina(repo)), repo


def test_set_documento_crea_un_item_por_pagina(qapp: object) -> None:
    documento = _documento(5)
    panel, _ = _panel(documento)

    panel.set_documento(documento)

    assert panel.count() == 5


def test_no_renderiza_todas_las_miniaturas_de_un_documento_grande(qapp: object) -> None:
    documento = _documento(200)
    panel, repo = _panel(documento)
    panel.resize(180, 400)
    panel.show()

    panel.set_documento(documento)

    assert len(panel.miniaturas_renderizadas()) < 200
    assert len(repo.render_llamadas) == len(panel.miniaturas_renderizadas())


def test_seleccionar_pagina_no_reemite_la_senal(qapp: object) -> None:
    documento = _documento(10)
    panel, _ = _panel(documento)
    panel.set_documento(documento)

    emitidas: list[int] = []
    panel.pagina_seleccionada.connect(emitidas.append)

    panel.seleccionar_pagina(4)

    assert panel.currentRow() == 4
    assert emitidas == []  # sincronización desde el visor, no debe re-emitir


def test_seleccion_del_usuario_emite_la_senal(qapp: object) -> None:
    documento = _documento(10)
    panel, _ = _panel(documento)
    panel.set_documento(documento)

    emitidas: list[int] = []
    panel.pagina_seleccionada.connect(emitidas.append)

    panel.setCurrentRow(3)  # simula clic del usuario

    assert emitidas == [3]
