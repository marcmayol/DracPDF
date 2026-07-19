"""Tests del RegistroDocumentos compartido."""

from __future__ import annotations

import fitz
import pytest

from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.errores import DocumentoNoAbierto


def test_registrar_y_obtener() -> None:
    registro = RegistroDocumentos()
    doc = fitz.open()
    doc.new_page()

    documento_id = registro.registrar(doc)

    assert documento_id in registro
    assert registro.obtener(documento_id) is doc
    registro.cerrar(documento_id)


def test_obtener_id_inexistente_lanza_documento_no_abierto() -> None:
    registro = RegistroDocumentos()

    with pytest.raises(DocumentoNoAbierto):
        registro.obtener("id-inexistente")


def test_cerrar_es_idempotente_y_libera() -> None:
    registro = RegistroDocumentos()
    doc = fitz.open()
    doc.new_page()
    documento_id = registro.registrar(doc)

    registro.cerrar(documento_id)
    registro.cerrar(documento_id)  # segunda vez no falla

    assert documento_id not in registro
    with pytest.raises(DocumentoNoAbierto):
        registro.obtener(documento_id)


def test_dos_adaptadores_comparten_el_mismo_documento() -> None:
    """El registro permite que varios adaptadores vean el mismo fitz.Document."""
    registro = RegistroDocumentos()
    doc = fitz.open()
    doc.new_page()
    documento_id = registro.registrar(doc)

    # Dos consumidores distintos del mismo registro obtienen el mismo objeto.
    assert registro.obtener(documento_id) is registro.obtener(documento_id)
    registro.cerrar(documento_id)
