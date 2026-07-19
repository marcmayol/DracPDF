"""Tests de integración de PyMuPDFFormService con PDFs de fixture reales."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.form_service import PyMuPDFFormService
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.formularios import CampoFormulario, TipoCampo


def _abrir(ruta: Path) -> tuple[PyMuPDFFormService, str, RegistroDocumentos]:
    registro = RegistroDocumentos()
    repo = PyMuPDFDocumentRepository(registro)
    servicio = PyMuPDFFormService(registro)
    documento = repo.abrir(ruta)
    return servicio, documento.id, registro


def _por_nombre(campos: tuple[CampoFormulario, ...], nombre: str) -> CampoFormulario:
    return next(c for c in campos if c.nombre == nombre)


def test_listar_campos_detecta_cada_tipo(pdf_formulario: Path) -> None:
    servicio, doc_id, registro = _abrir(pdf_formulario)

    campos = servicio.listar_campos(doc_id)
    tipos = {c.nombre: c.tipo for c in campos}

    assert tipos["nombre"] == TipoCampo.TEXTO
    assert tipos["acepta"] == TipoCampo.CASILLA
    assert tipos["pais"] == TipoCampo.COMBO
    assert tipos["color"] == TipoCampo.LISTA
    assert tipos["genero"] == TipoCampo.RADIO
    registro.cerrar(doc_id)


def test_combo_y_lista_exponen_sus_opciones(pdf_formulario: Path) -> None:
    servicio, doc_id, registro = _abrir(pdf_formulario)

    campos = servicio.listar_campos(doc_id)

    assert _por_nombre(campos, "pais").opciones == ("ES", "FR", "IT")
    assert _por_nombre(campos, "color").opciones == ("rojo", "verde", "azul")
    registro.cerrar(doc_id)


def test_casilla_expone_su_estado_on(pdf_formulario: Path) -> None:
    servicio, doc_id, registro = _abrir(pdf_formulario)

    acepta = _por_nombre(servicio.listar_campos(doc_id), "acepta")

    assert acepta.estado_activado is not None
    assert acepta.valor == "Off"  # sin marcar: distinto de estado_activado
    assert acepta.valor != acepta.estado_activado
    registro.cerrar(doc_id)


def test_radio_aparece_como_dos_campos_del_mismo_nombre(pdf_formulario: Path) -> None:
    servicio, doc_id, registro = _abrir(pdf_formulario)

    radios = [c for c in servicio.listar_campos(doc_id) if c.nombre == "genero"]

    assert len(radios) == 2
    assert all(c.tipo == TipoCampo.RADIO for c in radios)
    assert radios[0].id != radios[1].id
    registro.cerrar(doc_id)


def test_detecta_campo_de_solo_lectura(pdf_formulario: Path) -> None:
    servicio, doc_id, registro = _abrir(pdf_formulario)

    referencia = _por_nombre(servicio.listar_campos(doc_id), "referencia")

    assert referencia.solo_lectura is True
    registro.cerrar(doc_id)


def test_rect_en_puntos_pdf(pdf_formulario: Path) -> None:
    servicio, doc_id, registro = _abrir(pdf_formulario)

    nombre = _por_nombre(servicio.listar_campos(doc_id), "nombre")

    assert nombre.rect_pt.x0 == 50
    assert nombre.rect_pt.y0 == 50
    registro.cerrar(doc_id)


def test_es_xfa_true_para_documento_xfa(pdf_xfa: Path) -> None:
    servicio, doc_id, registro = _abrir(pdf_xfa)

    assert servicio.es_xfa(doc_id) is True
    registro.cerrar(doc_id)


def test_es_xfa_false_para_formulario_acroform(pdf_formulario: Path) -> None:
    servicio, doc_id, registro = _abrir(pdf_formulario)

    assert servicio.es_xfa(doc_id) is False
    registro.cerrar(doc_id)
