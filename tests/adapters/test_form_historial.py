"""Tests de integración de deshacer/rehacer del adaptador de formularios."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.form_service import PyMuPDFFormService
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.formularios import CampoFormulario
from tests.adapters.generar_fixtures_formularios import generar_formulario_dos_textos


def _abrir(ruta: Path) -> tuple[PyMuPDFFormService, str, RegistroDocumentos]:
    registro = RegistroDocumentos()
    servicio = PyMuPDFFormService(registro)
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    return servicio, documento.id, registro


def _id(campos: tuple[CampoFormulario, ...], nombre: str) -> str:
    return next(c.id for c in campos if c.nombre == nombre)


def _valor(servicio: PyMuPDFFormService, doc_id: str, campo_id: str) -> str:
    return next(c.valor for c in servicio.listar_campos(doc_id) if c.id == campo_id)


def test_deshacer_dos_campos_restaura_en_orden(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(
        generar_formulario_dos_textos(tmp_path / "dos.pdf")
    )
    a_id = _id(servicio.listar_campos(doc_id), "a")
    b_id = _id(servicio.listar_campos(doc_id), "b")

    servicio.escribir_valor(doc_id, a_id, "Marc")
    servicio.escribir_valor(doc_id, b_id, "Mayol")

    cambio = servicio.deshacer(doc_id)  # deshace b (el último)
    assert cambio is not None and cambio.campo_id == b_id and cambio.valor == "Y"
    assert _valor(servicio, doc_id, b_id) == "Y"
    assert _valor(servicio, doc_id, a_id) == "Marc"  # a sigue editado

    servicio.deshacer(doc_id)  # deshace a
    assert _valor(servicio, doc_id, a_id) == "X"
    registro.cerrar(doc_id)


def test_rehacer_restaura_el_valor(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(
        generar_formulario_dos_textos(tmp_path / "dos.pdf")
    )
    a_id = _id(servicio.listar_campos(doc_id), "a")

    servicio.escribir_valor(doc_id, a_id, "Marc")
    servicio.deshacer(doc_id)
    assert _valor(servicio, doc_id, a_id) == "X"

    servicio.rehacer(doc_id)
    assert _valor(servicio, doc_id, a_id) == "Marc"
    registro.cerrar(doc_id)


def test_el_historial_se_descarta_al_cerrar(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(
        generar_formulario_dos_textos(tmp_path / "dos.pdf")
    )
    a_id = _id(servicio.listar_campos(doc_id), "a")
    servicio.escribir_valor(doc_id, a_id, "Marc")
    assert servicio.puede_deshacer(doc_id) is True

    registro.cerrar(doc_id)
    assert servicio.puede_deshacer(doc_id) is False  # historial nuevo, vacío
