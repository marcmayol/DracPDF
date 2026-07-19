"""Tests del controlador de colocación de firma (SignatureLayer)."""

from __future__ import annotations

from pathlib import Path

import fitz

from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.estampar_firma import EstamparFirma
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.signature.signature_layer import SignatureLayer
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget
from tests.core.fakes import FakeDocumentRepository, FakeEstampadoService


def _png() -> bytes:
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 120, 50), False)
    pix.clear_with(180)
    return pix.tobytes("png")


_PNG_1x1 = _png()


def _documento(num_paginas: int = 3) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(
            Pagina(indice=i, ancho_pt=400.0, alto_pt=600.0) for i in range(num_paginas)
        ),
    )


def _entorno(
    documento: Documento,
) -> tuple[ViewerWidget, SignatureLayer, FakeEstampadoService, FakeDocumentRepository]:
    imagen = ImagenRenderizada(
        ancho_px=400, alto_px=600, datos=b"\x00" * (400 * 600 * 4), escala=1.0
    )
    repo = FakeDocumentRepository(documento=documento, imagen=imagen)
    visor = ViewerWidget(RenderizarPagina(repo))
    visor.resize(500, 700)
    servicio = FakeEstampadoService()
    capa = SignatureLayer(visor, EstamparFirma(servicio))
    return visor, capa, servicio, repo


def test_iniciar_colocacion_activa_el_modo(qapp: object) -> None:
    documento = _documento()
    visor, capa, _, _ = _entorno(documento)
    visor.set_documento(documento)

    capa.iniciar_colocacion(documento, _PNG_1x1)

    assert capa.colocando() is True


def test_cancelar_desactiva_el_modo(qapp: object) -> None:
    documento = _documento()
    visor, capa, _, _ = _entorno(documento)
    visor.set_documento(documento)
    capa.iniciar_colocacion(documento, _PNG_1x1)

    capa.cancelar()

    assert capa.colocando() is False


def test_confirmar_estampa_en_la_pagina_actual(qapp: object) -> None:
    documento = _documento()
    visor, capa, servicio, _ = _entorno(documento)
    visor.set_documento(documento)
    capa.iniciar_colocacion(documento, _PNG_1x1)

    pagina = capa.confirmar()

    assert pagina == 0
    assert len(servicio.estampados) == 1
    doc_id, pag, rect_pt, png = servicio.estampados[0]
    assert (doc_id, pag) == ("doc-1", 0)
    assert png == _PNG_1x1
    # El rectángulo cae dentro de la página (0..400 x 0..600 en puntos).
    assert 0 <= rect_pt.x0 < rect_pt.x1 <= 400
    assert 0 <= rect_pt.y0 < rect_pt.y1 <= 600
    assert capa.colocando() is False


def test_confirmar_invalida_el_render_de_la_pagina(qapp: object) -> None:
    documento = _documento()
    visor, capa, _, repo = _entorno(documento)
    visor.set_documento(documento)
    renders_antes = sum(1 for (_, i, _) in repo.render_llamadas if i == 0)

    capa.iniciar_colocacion(documento, _PNG_1x1)
    capa.confirmar()

    renders_despues = sum(1 for (_, i, _) in repo.render_llamadas if i == 0)
    assert renders_despues == renders_antes + 1  # se re-renderizó la página


def test_redimensionar_y_mover_antes_de_confirmar(qapp: object) -> None:
    from PySide6.QtCore import QPointF

    documento = _documento()
    visor, capa, servicio, _ = _entorno(documento)
    visor.set_documento(documento)
    capa.iniciar_colocacion(documento, _PNG_1x1)

    # El usuario redimensiona y mueve la previsualización antes de confirmar.
    item = capa._item
    assert item is not None
    item.redimensionar_desde_ancho(120.0)
    ancho, alto = item.tamano()
    # Colocar la esquina superior izquierda del item en (40, 30) de la página 0.
    rect_pagina = visor.rect_pagina(0)
    assert rect_pagina is not None
    item.setPos(QPointF(rect_pagina.left() + 40.0, rect_pagina.top() + 30.0))

    pagina = capa.confirmar()

    assert pagina == 0
    _, _, rect_pt, _ = servicio.estampados[0]
    # A escala 1.0, el rect en puntos coincide con el desplazamiento y tamaño.
    assert rect_pt.x0 == 40.0
    assert rect_pt.y0 == 30.0
    assert rect_pt.x1 == 40.0 + ancho
    assert rect_pt.y1 == 30.0 + alto


def test_confirmar_sin_colocar_no_hace_nada(qapp: object) -> None:
    documento = _documento()
    visor, capa, servicio, _ = _entorno(documento)
    visor.set_documento(documento)

    assert capa.confirmar() is None
    assert servicio.estampados == []
