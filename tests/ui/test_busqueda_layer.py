"""Tests de BusquedaLayer: resaltado de coincidencias sobre el visor."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

from lectorpdf.core.domain.contenido import Coincidencia
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.busqueda.busqueda_layer import BusquedaLayer
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget
from tests.core.fakes import FakeDocumentRepository


def _documento(num_paginas: int = 2) -> Documento:
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


def _coincidencias() -> tuple[Coincidencia, ...]:
    return (
        Coincidencia(0, RectanguloPt(50, 60, 150, 80)),
        Coincidencia(1, RectanguloPt(50, 60, 150, 80)),
    )


def test_crea_un_item_por_coincidencia(qapp: object) -> None:
    documento = _documento()
    visor = _visor(documento)
    capa = BusquedaLayer(visor)
    visor.set_documento(documento)

    capa.set_coincidencias(_coincidencias(), activa=0)

    assert len(capa.items()) == 2


def test_la_activa_tiene_borde_y_el_resto_no(qapp: object) -> None:
    documento = _documento()
    visor = _visor(documento)
    capa = BusquedaLayer(visor)
    visor.set_documento(documento)

    capa.set_coincidencias(_coincidencias(), activa=1)

    items = capa.items()
    assert items[0].pen().style() == Qt.PenStyle.NoPen  # resto sin borde
    assert items[1].pen().style() != Qt.PenStyle.NoPen  # activa con borde


def test_limpiar_borra_los_items(qapp: object) -> None:
    documento = _documento()
    visor = _visor(documento)
    capa = BusquedaLayer(visor)
    visor.set_documento(documento)
    capa.set_coincidencias(_coincidencias(), activa=0)

    capa.limpiar()

    assert capa.items() == []


def test_se_redibuja_tras_reconstruir_la_escena(qapp: object) -> None:
    documento = _documento()
    visor = _visor(documento)
    capa = BusquedaLayer(visor)
    visor.set_documento(documento)
    capa.set_coincidencias(_coincidencias(), activa=0)

    # El zoom reconstruye la escena (destruye los items previos): deben volver.
    visor.set_escala(1.5)

    assert len(capa.items()) == 2
