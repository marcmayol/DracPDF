"""Tests de verificación de firmas del adaptador pyHanko (sin red)."""

from __future__ import annotations

from pathlib import Path

import fitz

from lectorpdf.adapters.pyhanko.signature_service import PyHankoSignatureService
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.firma_digital import (
    ConfigFirma,
    CredencialPKCS12,
    EstadoFirma,
)


def _pdf(tmp_path: Path) -> Path:
    ruta = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page(width=400, height=300)
    doc.save(ruta)
    doc.close()
    return ruta


def _firmar(ruta: Path, p12: Path, pwd: str) -> None:
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    PyHankoSignatureService(registro).firmar(
        documento.id, ConfigFirma(pagina=0), CredencialPKCS12(p12, pwd)
    )
    registro.cerrar(documento.id)


def _verificar(ruta: Path, anclas: list[Path]) -> tuple:  # type: ignore[type-arg]
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    resultados = PyHankoSignatureService(registro).verificar(documento.id, anclas)
    registro.cerrar(documento.id)
    return resultados


def test_firma_valida_con_ancla_de_confianza(
    tmp_path: Path, certificado: tuple[Path, Path, str]
) -> None:
    p12, der, pwd = certificado
    ruta = _pdf(tmp_path)
    _firmar(ruta, p12, pwd)

    resultados = _verificar(ruta, [der])

    assert len(resultados) == 1
    assert resultados[0].estado == EstadoFirma.VALIDA
    assert resultados[0].cubre_todo_el_documento is True
    assert resultados[0].sellada_en_tiempo is False  # sin TSA


def test_firma_sin_ancla_es_desconocida(
    tmp_path: Path, certificado: tuple[Path, Path, str]
) -> None:
    p12, _, pwd = certificado
    ruta = _pdf(tmp_path)
    _firmar(ruta, p12, pwd)

    resultados = _verificar(ruta, [])  # sin anclas de confianza

    assert resultados[0].estado == EstadoFirma.DESCONOCIDA


def test_documento_modificado_tras_la_firma_es_invalido(
    tmp_path: Path, certificado: tuple[Path, Path, str]
) -> None:
    p12, der, pwd = certificado
    ruta = _pdf(tmp_path)
    _firmar(ruta, p12, pwd)

    # Manipulación: añadir contenido como revisión incremental tras la firma.
    doc = fitz.open(ruta)
    doc[0].insert_text((40, 120), "TEXTO ANADIDO TRAS LA FIRMA", fontsize=12)
    doc.save(ruta, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()

    resultados = _verificar(ruta, [der])

    assert resultados[0].estado == EstadoFirma.INVALIDA
    assert resultados[0].cubre_todo_el_documento is False


def test_documento_sin_firmas_no_da_resultados(tmp_path: Path) -> None:
    resultados = _verificar(_pdf(tmp_path), [])

    assert resultados == ()
