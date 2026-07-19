"""Tests de escritura y guardado incremental del adaptador de formularios."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.form_service import PyMuPDFFormService
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.errores import CampoNoEncontrado
from lectorpdf.core.domain.formularios import CampoFormulario


def _abrir(ruta: Path) -> tuple[PyMuPDFFormService, str, RegistroDocumentos]:
    registro = RegistroDocumentos()
    repo = PyMuPDFDocumentRepository(registro)
    servicio = PyMuPDFFormService(registro)
    documento = repo.abrir(ruta)
    return servicio, documento.id, registro


def _id_de(campos: tuple[CampoFormulario, ...], nombre: str) -> str:
    return next(c.id for c in campos if c.nombre == nombre)


def test_escribir_marca_el_documento_como_sucio(pdf_formulario: Path) -> None:
    servicio, doc_id, registro = _abrir(pdf_formulario)
    campo_id = _id_de(servicio.listar_campos(doc_id), "nombre")

    assert servicio.esta_sucio(doc_id) is False
    servicio.escribir_valor(doc_id, campo_id, "Marc")
    assert servicio.esta_sucio(doc_id) is True
    registro.cerrar(doc_id)


def test_guardar_incremental_y_reabrir_conserva_los_valores(
    pdf_formulario: Path,
) -> None:
    servicio, doc_id, registro = _abrir(pdf_formulario)
    campos = servicio.listar_campos(doc_id)

    servicio.escribir_valor(doc_id, _id_de(campos, "nombre"), "Marc")
    servicio.escribir_valor(doc_id, _id_de(campos, "pais"), "FR")
    servicio.escribir_valor(doc_id, _id_de(campos, "color"), "verde")
    acepta = next(c for c in campos if c.nombre == "acepta")
    assert acepta.estado_activado is not None
    servicio.escribir_valor(doc_id, acepta.id, acepta.estado_activado)

    servicio.guardar_incremental(doc_id, None)  # incremental in situ
    assert servicio.esta_sucio(doc_id) is False
    registro.cerrar(doc_id)

    # Reabrir con un registro/servicio nuevos: los valores deben persistir.
    servicio2, doc_id2, registro2 = _abrir(pdf_formulario)
    valores = {c.nombre: c.valor for c in servicio2.listar_campos(doc_id2)}

    assert valores["nombre"] == "Marc"
    assert valores["pais"] == "FR"
    assert valores["color"] == "verde"
    assert valores["acepta"] == acepta.estado_activado
    registro2.cerrar(doc_id2)


def test_escribir_id_inexistente_lanza_campo_no_encontrado(
    pdf_formulario: Path,
) -> None:
    servicio, doc_id, registro = _abrir(pdf_formulario)

    with pytest.raises(CampoNoEncontrado):
        servicio.escribir_valor(doc_id, "9:9", "x")
    with pytest.raises(CampoNoEncontrado):
        servicio.escribir_valor(doc_id, "no-es-id", "x")
    registro.cerrar(doc_id)
