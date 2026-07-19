"""Tests del bloqueo de edición cuando el documento está firmado (Marca.FIRMADO)."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.estampado_service import PyMuPDFEstampadoService
from lectorpdf.adapters.pymupdf.form_service import PyMuPDFFormService
from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.errores import DocumentoFirmado
from lectorpdf.core.domain.formularios import RectanguloPt


def test_editar_campo_de_documento_firmado_se_rechaza(pdf_formulario: Path) -> None:
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(pdf_formulario)
    servicio = PyMuPDFFormService(registro)
    campo = servicio.listar_campos(documento.id)[0]

    registro.marcar(documento.id, Marca.FIRMADO)  # simula documento firmado

    with pytest.raises(DocumentoFirmado):
        servicio.escribir_valor(documento.id, campo.id, "x")
    registro.cerrar(documento.id)


def test_estampar_en_documento_firmado_se_rechaza(pdf_formulario: Path) -> None:
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(pdf_formulario)
    servicio = PyMuPDFEstampadoService(registro)

    registro.marcar(documento.id, Marca.FIRMADO)

    with pytest.raises(DocumentoFirmado):
        servicio.estampar_imagen(documento.id, 0, RectanguloPt(0, 0, 10, 10), b"x")
    registro.cerrar(documento.id)


def test_firmar_de_verdad_bloquea_ediciones_posteriores(
    tmp_path: Path, certificado: tuple[Path, Path, str]
) -> None:
    import fitz

    from lectorpdf.adapters.pyhanko.signature_service import PyHankoSignatureService
    from lectorpdf.core.domain.firma_digital import ConfigFirma, CredencialPKCS12

    p12, _, pwd = certificado
    ruta = tmp_path / "doc.pdf"
    d = fitz.open()
    d.new_page(width=300, height=300)
    d.save(ruta)
    d.close()

    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    PyHankoSignatureService(registro).firmar(
        documento.id, ConfigFirma(pagina=0), CredencialPKCS12(p12, pwd)
    )

    # Tras firmar, estampar debe rechazarse.
    with pytest.raises(DocumentoFirmado):
        PyMuPDFEstampadoService(registro).estampar_imagen(
            documento.id, 0, RectanguloPt(0, 0, 10, 10), b"x"
        )
    registro.cerrar(documento.id)
