"""Tests de integración de PyMuPDFContenido (búsqueda, Fase 8)."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.adapters.pymupdf.contenido import PyMuPDFContenido
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos


def _abrir(ruta: Path) -> tuple[PyMuPDFContenido, str]:
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    return PyMuPDFContenido(registro), documento.id


def test_buscar_encuentra_todas_las_ocurrencias(pdf_contenido: Path) -> None:
    servicio, doc_id = _abrir(pdf_contenido)

    coincidencias = servicio.buscar(doc_id, "Ladon")

    # 2 en la página 1, 1 en la 2 (0-based: páginas 0 y 1).
    assert len(coincidencias) == 3
    assert [c.pagina for c in coincidencias] == [0, 0, 1]
    for c in coincidencias:
        assert c.rect_pt.ancho > 0 and c.rect_pt.alto > 0


def test_buscar_es_insensible_a_mayusculas_por_defecto(pdf_contenido: Path) -> None:
    servicio, doc_id = _abrir(pdf_contenido)
    assert len(servicio.buscar(doc_id, "ladon")) == 3


def test_buscar_distinguiendo_mayusculas_filtra(pdf_contenido: Path) -> None:
    servicio, doc_id = _abrir(pdf_contenido)

    # "Ladon" con mayúscula inicial existe (3); "ladon" en minúsculas no.
    assert len(servicio.buscar(doc_id, "Ladon", coincidir_mayusculas=True)) == 3
    assert servicio.buscar(doc_id, "ladon", coincidir_mayusculas=True) == ()


def test_buscar_sin_resultados(pdf_contenido: Path) -> None:
    servicio, doc_id = _abrir(pdf_contenido)
    assert servicio.buscar(doc_id, "inexistente_zzz") == ()


def test_buscar_reporta_progreso_por_pagina(pdf_contenido: Path) -> None:
    servicio, doc_id = _abrir(pdf_contenido)
    hechos: list[tuple[int, int]] = []

    servicio.buscar(doc_id, "Ladon", progreso=lambda h, t: hechos.append((h, t)))

    assert hechos == [(1, 3), (2, 3), (3, 3)]  # 3 páginas


def test_indice_coincide_con_get_toc(pdf_contenido: Path) -> None:
    servicio, doc_id = _abrir(pdf_contenido)

    entradas = servicio.indice(doc_id)

    # get_toc del fixture: Portada(1), Introduccion(2), Desarrollo(1), Cierre(1)
    # con páginas 1,1,2,3 (1-based) -> 0,0,1,2 (0-based).
    assert [(e.nivel, e.titulo, e.pagina) for e in entradas] == [
        (1, "Portada", 0),
        (2, "Introduccion", 0),
        (1, "Desarrollo", 1),
        (1, "Cierre", 2),
    ]


def test_indice_vacio_si_no_hay_outline(pdf_simple: Path) -> None:
    servicio, doc_id = _abrir(pdf_simple)
    assert servicio.indice(doc_id) == ()


def test_enlaces_interno_y_externo(pdf_contenido: Path) -> None:
    servicio, doc_id = _abrir(pdf_contenido)

    enlaces = servicio.enlaces(doc_id, 0)

    internos = [e for e in enlaces if not e.es_externo]
    externos = [e for e in enlaces if e.es_externo]
    assert any(e.pagina_destino == 1 for e in internos)  # GOTO a la página 2
    assert any(e.uri == "https://example.com/" for e in externos)


def test_enlaces_pagina_sin_enlaces(pdf_contenido: Path) -> None:
    servicio, doc_id = _abrir(pdf_contenido)
    assert servicio.enlaces(doc_id, 2) == ()


def test_propiedades_lee_metadatos_y_datos_tecnicos(pdf_contenido: Path) -> None:
    servicio, doc_id = _abrir(pdf_contenido)

    props = servicio.propiedades(doc_id)

    assert props.titulo == "Documento Ladon"
    assert props.autor == "Marc Mayol"
    assert props.num_paginas == 3
    assert props.version_pdf.startswith("PDF")
    assert props.cifrado is False
    assert props.tamano_bytes == pdf_contenido.stat().st_size


def test_palabras_en_orden_de_lectura(pdf_contenido: Path) -> None:
    servicio, doc_id = _abrir(pdf_contenido)

    palabras = servicio.palabras(doc_id, 0)
    textos = [p.texto for p in palabras]

    # La frase de la segunda línea aparece consecutiva y en orden.
    i = textos.index("frase")
    assert textos[i : i + 3] == ["frase", "exacta", "seleccionable"]
    for p in palabras:
        assert p.rect_pt.ancho > 0 and p.rect_pt.alto > 0
