"""Tests de SeleccionLayer: resaltado, texto seleccionado y copia."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.contenido import PalabraTexto
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.obtener_palabras import ObtenerPalabras
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.seleccion.seleccion_layer import SeleccionLayer
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget
from tests.core.fakes import FakeDocumentRepository


class _FakeTexto:
    def __init__(self, por_pagina: dict[int, tuple[PalabraTexto, ...]]) -> None:
        self._por_pagina = por_pagina

    def palabras(self, documento_id: str, pagina: int) -> tuple[PalabraTexto, ...]:
        return self._por_pagina.get(pagina, ())


def _palabra(texto: str, x0: float, bloque: int, linea: int) -> PalabraTexto:
    y0 = 60.0 + linea * 20.0
    return PalabraTexto(RectanguloPt(x0, y0, x0 + 20.0, y0 + 12.0), texto, bloque, linea)


def _pagina0() -> tuple[PalabraTexto, ...]:
    return (
        _palabra("frase", 50.0, 0, 0),
        _palabra("exacta", 75.0, 0, 0),
        _palabra("seleccionable", 105.0, 0, 0),
    )


def _documento() -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=(Pagina(0, 400.0, 600.0), Pagina(1, 400.0, 600.0)),
    )


def _montar() -> tuple[ViewerWidget, SeleccionLayer]:
    documento = _documento()
    imagen = ImagenRenderizada(
        ancho_px=400, alto_px=600, datos=b"\x00" * (400 * 600 * 4), escala=1.0
    )
    visor = ViewerWidget(RenderizarPagina(FakeDocumentRepository(documento, imagen)))
    caso = ObtenerPalabras(_FakeTexto({0: _pagina0()}))
    capa = SeleccionLayer(visor, caso)
    capa.set_documento(documento)
    visor.set_documento(documento)
    return visor, capa


def test_seleccionar_rango_arrastrado_da_el_texto(qapp: object) -> None:
    _, capa = _montar()

    # Ancla en "frase" (idx 0) y arrastre hasta "seleccionable" (idx 2).
    capa._iniciar_arrastre(0, 55.0, 66.0)
    capa._extender_arrastre(110.0, 66.0)

    assert capa.texto_seleccionado() == "frase exacta seleccionable"
    assert len(capa.items()) == 3


def test_doble_clic_selecciona_una_palabra(qapp: object) -> None:
    _, capa = _montar()

    capa._seleccionar_palabra(0, 80.0, 66.0)  # sobre "exacta"

    assert capa.texto_seleccionado() == "exacta"
    assert len(capa.items()) == 1


def test_triple_clic_selecciona_el_parrafo(qapp: object) -> None:
    _, capa = _montar()

    capa._seleccionar_parrafo(0, 80.0, 66.0)

    assert capa.texto_seleccionado() == "frase exacta seleccionable"


def test_copiar_pone_el_texto_en_el_portapapeles(qapp: object) -> None:
    from PySide6.QtGui import QGuiApplication

    _, capa = _montar()
    capa._iniciar_arrastre(0, 55.0, 66.0)
    capa._extender_arrastre(80.0, 66.0)  # "frase exacta"

    copiado = capa.copiar()

    assert copiado == "frase exacta"
    portapapeles = QGuiApplication.clipboard()
    assert portapapeles is not None
    assert portapapeles.text() == "frase exacta"


def test_seleccionar_todo_abarca_toda_la_pagina(qapp: object) -> None:
    _, capa = _montar()

    capa.seleccionar_todo(0)

    assert capa.texto_seleccionado() == "frase exacta seleccionable"
    assert len(capa.items()) == 3


def test_limpiar_borra_la_seleccion(qapp: object) -> None:
    _, capa = _montar()
    capa._seleccionar_parrafo(0, 80.0, 66.0)

    capa.limpiar()

    assert capa.texto_seleccionado() == ""
    assert capa.items() == []


def test_seleccion_se_repinta_tras_zoom(qapp: object) -> None:
    visor, capa = _montar()
    capa._seleccionar_parrafo(0, 80.0, 66.0)

    visor.set_escala(1.5)  # reconstruye la escena

    assert len(capa.items()) == 3
