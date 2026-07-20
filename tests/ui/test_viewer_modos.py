"""Tests de los modos de vista del visor (Fase 8): ajuste persistente, doble
página y rotación de vista."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.viewer.viewer_widget import MARGEN_PX, ViewerWidget
from tests.core.fakes import FakeDocumentRepository


def _documento(num_paginas: int = 4) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(
            Pagina(indice=i, ancho_pt=100.0, alto_pt=200.0)
            for i in range(num_paginas)
        ),
    )


def _visor(documento: Documento) -> ViewerWidget:
    imagen = ImagenRenderizada(
        ancho_px=100, alto_px=200, datos=b"\x00" * (100 * 200 * 4), escala=1.0
    )
    visor = ViewerWidget(RenderizarPagina(FakeDocumentRepository(documento, imagen)))
    visor.resize(500, 400)
    return visor


def test_doble_pagina_coloca_dos_por_fila(qapp: object) -> None:
    documento = _documento(4)
    visor = _visor(documento)
    visor.set_documento(documento, escala=1.0)

    visor.set_doble_pagina(True)

    # Páginas 0 y 1 en la misma fila (mismo top); la 2 baja de fila.
    assert visor._geometria[0].top() == visor._geometria[1].top()
    assert visor._geometria[1].left() > visor._geometria[0].left()
    assert visor._geometria[2].top() > visor._geometria[0].top()


def test_rotacion_intercambia_ancho_y_alto(qapp: object) -> None:
    documento = _documento(1)
    visor = _visor(documento)
    visor.set_documento(documento, escala=1.0)

    visor.rotar_vista(90)

    assert visor.rotacion() == 90
    # 100x200 pt rotado 90 -> 200x100 en la geometría.
    assert visor._geometria[0].width() == 200.0
    assert visor._geometria[0].height() == 100.0


def test_ajuste_ancho_persiste_al_cambiar_tamano(qapp: object) -> None:
    documento = _documento(2)
    visor = _visor(documento)
    visor.set_documento(documento, escala=1.0)

    visor.ajustar_a_ancho()
    assert visor.modo_ajuste() == "ANCHO"

    visor.resize(800, 400)  # el modo se re-aplica al nuevo ancho
    esperado = (visor.viewport().width() - 2 * MARGEN_PX) / 100.0
    assert visor.escala == pytest.approx(esperado, rel=1e-3)


def test_zoom_manual_cancela_el_modo_de_ajuste(qapp: object) -> None:
    documento = _documento(2)
    visor = _visor(documento)
    visor.set_documento(documento, escala=1.0)
    visor.ajustar_a_ancho()

    visor.zoom_acercar()

    assert visor.modo_ajuste() == "LIBRE"


def test_emite_modo_ajuste_cambiado(qapp: object) -> None:
    documento = _documento(2)
    visor = _visor(documento)
    visor.set_documento(documento, escala=1.0)
    modos: list[str] = []
    visor.modo_ajuste_cambiado.connect(modos.append)

    visor.ajustar_a_pagina()
    visor.zoom_acercar()

    assert modos == ["PAGINA", "LIBRE"]


def test_set_modo_ajuste_restaura(qapp: object) -> None:
    documento = _documento(2)
    visor = _visor(documento)
    visor.set_documento(documento, escala=1.0)

    visor.set_modo_ajuste("ANCHO")

    assert visor.modo_ajuste() == "ANCHO"
