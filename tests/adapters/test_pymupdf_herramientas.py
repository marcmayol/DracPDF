"""Tests de integración de PyMuPDFHerramientas."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.herramientas import PyMuPDFHerramientas
from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.errores import DocumentoFirmado, SinPaginas


def _pdf(ruta: Path, textos: list[str]) -> Path:
    doc = fitz.open()
    for texto in textos:
        pagina = doc.new_page(width=300, height=400)
        pagina.insert_text((40, 60), texto, fontsize=14)
    doc.save(ruta)
    doc.close()
    return ruta


def _servicio() -> PyMuPDFHerramientas:
    return PyMuPDFHerramientas(RegistroDocumentos())


def _abrir(ruta: Path) -> tuple[PyMuPDFHerramientas, str, RegistroDocumentos]:
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    return PyMuPDFHerramientas(registro), documento.id, registro


def test_unir_respeta_el_orden(tmp_path: Path) -> None:
    a = _pdf(tmp_path / "a.pdf", ["A1", "A2"])
    b = _pdf(tmp_path / "b.pdf", ["B1"])
    destino = tmp_path / "unido.pdf"

    _servicio().unir([b, a], destino)  # b antes que a

    doc = fitz.open(destino)
    assert doc.page_count == 3
    assert doc[0].get_text().strip() == "B1"
    assert doc[1].get_text().strip() == "A1"
    doc.close()


def test_unir_reporta_progreso(tmp_path: Path) -> None:
    rutas = [
        _pdf(tmp_path / "a.pdf", ["A"]),
        _pdf(tmp_path / "b.pdf", ["B"]),
        _pdf(tmp_path / "c.pdf", ["C"]),
    ]
    progresos: list[tuple[int, int]] = []

    _servicio().unir(rutas, tmp_path / "u.pdf", lambda h, t: progresos.append((h, t)))

    assert progresos[-1] == (3, 3)


# -- Organizar páginas ------------------------------------------------------


def test_eliminar_pagina_reduce_y_marca_cambios(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path / "d.pdf", ["A", "B", "C"]))

    paginas = servicio.eliminar_pagina(doc_id, 1)

    assert len(paginas) == 2
    assert registro.tiene(doc_id, Marca.CAMBIOS_SIN_GUARDAR)
    registro.cerrar(doc_id)


def test_mover_pagina_reordena(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path / "d.pdf", ["A", "B", "C"]))

    servicio.mover_pagina(doc_id, 0, 2)  # A pasa al final

    doc = registro.obtener(doc_id)
    assert doc[2].get_text().strip() == "A"
    registro.cerrar(doc_id)


def test_rotar_pagina(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path / "d.pdf", ["A"]))

    servicio.rotar_pagina(doc_id, 0, 90)

    assert registro.obtener(doc_id)[0].rotation == 90
    registro.cerrar(doc_id)


def test_organizar_documento_firmado_se_rechaza(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path / "d.pdf", ["A", "B"]))
    registro.marcar(doc_id, Marca.FIRMADO)

    with pytest.raises(DocumentoFirmado):
        servicio.rotar_pagina(doc_id, 0, 90)
    with pytest.raises(DocumentoFirmado):
        servicio.eliminar_pagina(doc_id, 0)
    with pytest.raises(DocumentoFirmado):
        servicio.mover_pagina(doc_id, 0, 1)
    registro.cerrar(doc_id)


def test_no_se_puede_eliminar_la_ultima_pagina(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path / "d.pdf", ["única"]))

    with pytest.raises(SinPaginas):
        servicio.eliminar_pagina(doc_id, 0)
    registro.cerrar(doc_id)


# -- Dividir ----------------------------------------------------------------


def test_dividir_por_rangos_genera_ficheros(tmp_path: Path) -> None:
    from lectorpdf.core.domain.herramientas import Rango

    servicio, doc_id, registro = _abrir(_pdf(tmp_path / "d.pdf", ["A", "B", "C", "D"]))
    salida = tmp_path / "partes"

    rutas = servicio.dividir(doc_id, [Rango(1, 2), Rango(3, 4)], salida)

    assert len(rutas) == 2
    assert all(r.is_file() for r in rutas)
    parte1 = fitz.open(rutas[0])
    assert parte1.page_count == 2
    assert parte1[0].get_text().strip() == "A"
    parte1.close()
    registro.cerrar(doc_id)


# -- Proteger / desproteger -------------------------------------------------


def test_proteger_genera_pdf_cifrado(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path / "d.pdf", ["SECRETO"]))
    destino = tmp_path / "prot.pdf"

    servicio.proteger(doc_id, destino, "clave")

    reabierto = fitz.open(destino)
    assert reabierto.needs_pass
    assert reabierto.authenticate("clave")
    reabierto.close()
    registro.cerrar(doc_id)


def test_desproteger_con_contrasena_correcta(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path / "d.pdf", ["SECRETO"]))
    prot = tmp_path / "prot.pdf"
    servicio.proteger(doc_id, prot, "clave")
    registro.cerrar(doc_id)

    desp = tmp_path / "desp.pdf"
    _servicio().desproteger(prot, "clave", desp)

    reabierto = fitz.open(desp)
    assert not reabierto.needs_pass
    assert reabierto[0].get_text().strip() == "SECRETO"
    reabierto.close()


def test_desproteger_contrasena_incorrecta(tmp_path: Path) -> None:
    from lectorpdf.core.domain.errores import ContrasenaIncorrecta

    servicio, doc_id, registro = _abrir(_pdf(tmp_path / "d.pdf", ["S"]))
    prot = tmp_path / "prot.pdf"
    servicio.proteger(doc_id, prot, "clave")
    registro.cerrar(doc_id)

    with pytest.raises(ContrasenaIncorrecta):
        _servicio().desproteger(prot, "mala", tmp_path / "x.pdf")


# -- Comprimir --------------------------------------------------------------


def test_comprimir_reduce_el_tamano(tmp_path: Path) -> None:
    ruta = tmp_path / "grande.pdf"
    doc = fitz.open()
    for _ in range(40):
        pagina = doc.new_page()
        pagina.insert_text((40, 60), ("relleno " * 20 + " ") * 3, fontsize=10)
    doc.save(ruta)
    doc.close()

    servicio, doc_id, registro = _abrir(ruta)
    destino = tmp_path / "comp.pdf"

    resultado = servicio.comprimir(doc_id, destino)

    assert destino.is_file()
    assert resultado.bytes_despues < resultado.bytes_antes
    assert resultado.porcentaje_reduccion > 0
    registro.cerrar(doc_id)
