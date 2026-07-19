"""Tests de integración del adaptador de firma pyHanko (sin red / sin TSA)."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from lectorpdf.adapters.pyhanko.signature_service import PyHankoSignatureService
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.errores import CredencialInvalida, DocumentoFirmado
from lectorpdf.core.domain.firma_digital import ConfigFirma, CredencialPKCS12


def _pdf(tmp_path: Path) -> Path:
    ruta = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page(width=400, height=300)
    doc.save(ruta)
    doc.close()
    return ruta


def _abrir(
    ruta: Path,
) -> tuple[PyHankoSignatureService, str, RegistroDocumentos]:
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    return PyHankoSignatureService(registro), documento.id, registro


def test_firmar_deja_el_documento_firmado(
    tmp_path: Path, certificado: tuple[Path, Path, str]
) -> None:
    p12, _, pwd = certificado
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))

    assert registro.tiene(doc_id, Marca.FIRMADO) is False
    servicio.firmar(doc_id, ConfigFirma(pagina=0), CredencialPKCS12(p12, pwd))

    assert registro.tiene(doc_id, Marca.FIRMADO) is True
    # El fichero de disco tiene ahora una firma.
    reabierto = fitz.open(registro.ruta(doc_id))
    assert reabierto.get_sigflags() > 0
    reabierto.close()
    registro.cerrar(doc_id)


def test_refirmar_un_documento_firmado_se_rechaza(
    tmp_path: Path, certificado: tuple[Path, Path, str]
) -> None:
    p12, _, pwd = certificado
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    servicio.firmar(doc_id, ConfigFirma(pagina=0), CredencialPKCS12(p12, pwd))

    with pytest.raises(DocumentoFirmado):
        servicio.firmar(doc_id, ConfigFirma(pagina=0), CredencialPKCS12(p12, pwd))
    registro.cerrar(doc_id)


def test_contrasena_incorrecta_es_credencial_invalida(
    tmp_path: Path, certificado: tuple[Path, Path, str]
) -> None:
    p12, _, _ = certificado
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))

    with pytest.raises(CredencialInvalida):
        servicio.firmar(doc_id, ConfigFirma(pagina=0), CredencialPKCS12(p12, "mala"))
    registro.cerrar(doc_id)


def test_abrir_un_pdf_ya_firmado_lo_marca_firmado(
    tmp_path: Path, certificado: tuple[Path, Path, str]
) -> None:
    p12, _, pwd = certificado
    ruta = _pdf(tmp_path)
    # Firmar y cerrar.
    servicio, doc_id, registro = _abrir(ruta)
    servicio.firmar(doc_id, ConfigFirma(pagina=0), CredencialPKCS12(p12, pwd))
    registro.cerrar(doc_id)

    # Reabrir en una sesión nueva: debe detectarse como firmado.
    registro2 = RegistroDocumentos()
    documento2 = PyMuPDFDocumentRepository(registro2).abrir(ruta)
    assert registro2.tiene(documento2.id, Marca.FIRMADO) is True
    registro2.cerrar(documento2.id)
