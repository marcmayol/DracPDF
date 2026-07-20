"""Tests de la lógica pura de la lista de documentos recientes (sin Qt)."""

from __future__ import annotations

from lectorpdf.ui import recientes


def test_anadir_pone_al_frente_sin_duplicados() -> None:
    lista = recientes.anadir(["b.pdf", "a.pdf"], "a.pdf")
    assert lista == ["a.pdf", "b.pdf"]


def test_anadir_recorta_al_maximo() -> None:
    actuales = [f"{i}.pdf" for i in range(10)]
    lista = recientes.anadir(actuales, "nuevo.pdf", maximo=5)
    assert len(lista) == 5
    assert lista[0] == "nuevo.pdf"


def test_elidir_deja_corta_la_ruta_corta() -> None:
    assert recientes.elidir("C:/a.pdf", maximo=50) == "C:/a.pdf"


def test_elidir_acorta_por_el_centro() -> None:
    ruta = "C:/Users/marc/documentos/muy/larga/ruta/documento_final.pdf"
    elidida = recientes.elidir(ruta, maximo=25)
    assert len(elidida) == 25
    assert "…" in elidida
    assert elidida.startswith("C:/Users")
    assert elidida.endswith(".pdf")
