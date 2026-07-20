"""Tests de EnlacesLayer: detección de enlace y emisión de señales."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.contenido import Enlace
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.obtener_enlaces import ObtenerEnlaces
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.enlaces.enlaces_layer import EnlacesLayer
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget
from tests.core.fakes import FakeDocumentRepository


class _FakeEnlaces:
    def __init__(self, por_pagina: dict[int, tuple[Enlace, ...]]) -> None:
        self._por_pagina = por_pagina

    def enlaces(self, documento_id: str, pagina: int) -> tuple[Enlace, ...]:
        return self._por_pagina.get(pagina, ())


def _documento() -> Documento:
    return Documento(
        id="doc-1", ruta=Path("d.pdf"), paginas=(Pagina(0, 400.0, 600.0),)
    )


def _montar(enlaces: tuple[Enlace, ...]) -> EnlacesLayer:
    documento = _documento()
    imagen = ImagenRenderizada(
        ancho_px=400, alto_px=600, datos=b"\x00" * (400 * 600 * 4), escala=1.0
    )
    visor = ViewerWidget(RenderizarPagina(FakeDocumentRepository(documento, imagen)))
    capa = EnlacesLayer(visor, ObtenerEnlaces(_FakeEnlaces({0: enlaces})))
    capa.set_documento(documento)
    visor.set_documento(documento)
    return capa


def test_enlace_en_detecta_por_rect() -> None:
    interno = Enlace(RectanguloPt(50, 60, 150, 80), pagina_destino=3)
    capa = _montar((interno,))

    assert capa.enlace_en(0, 100.0, 70.0) is interno
    assert capa.enlace_en(0, 300.0, 300.0) is None


def test_activar_interno_emite_navegar() -> None:
    interno = Enlace(RectanguloPt(50, 60, 150, 80), pagina_destino=3)
    capa = _montar((interno,))
    paginas: list[int] = []
    capa.navegar_interno.connect(paginas.append)

    capa._activar(interno)

    assert paginas == [3]


def test_activar_externo_emite_uri() -> None:
    externo = Enlace(RectanguloPt(50, 90, 150, 110), uri="https://example.com/")
    capa = _montar((externo,))
    uris: list[str] = []
    capa.abrir_externo.connect(uris.append)

    capa._activar(externo)

    assert uris == ["https://example.com/"]
