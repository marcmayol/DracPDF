"""Tests del caso de uso RenderizarPagina con un fake del repositorio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from tests.core.fakes import FakeDocumentRepository


def _documento(num_paginas: int = 3) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(
            Pagina(indice=i, ancho_pt=595.0, alto_pt=842.0) for i in range(num_paginas)
        ),
    )


def test_renderiza_pagina_valida_y_delega_con_id_indice_y_escala() -> None:
    documento = _documento()
    imagen = ImagenRenderizada(ancho_px=10, alto_px=20, datos=b"\x00" * 800, escala=2.0)
    repo = FakeDocumentRepository(documento=documento, imagen=imagen)

    resultado = RenderizarPagina(repo).ejecutar(documento, indice=1, escala=2.0)

    assert resultado is imagen
    assert repo.render_llamado_con == ("doc-1", 1, 2.0)


@pytest.mark.parametrize("indice", [-1, 3, 99])
def test_indice_fuera_de_rango_lanza_pagina_fuera_de_rango(indice: int) -> None:
    documento = _documento(num_paginas=3)
    repo = FakeDocumentRepository(documento=documento)

    with pytest.raises(PaginaFueraDeRango):
        RenderizarPagina(repo).ejecutar(documento, indice=indice, escala=1.0)

    assert repo.render_llamado_con is None


@pytest.mark.parametrize("escala", [0.0, -1.0])
def test_escala_no_positiva_lanza_value_error(escala: float) -> None:
    documento = _documento()
    repo = FakeDocumentRepository(documento=documento)

    with pytest.raises(ValueError):
        RenderizarPagina(repo).ejecutar(documento, indice=0, escala=escala)

    assert repo.render_llamado_con is None
