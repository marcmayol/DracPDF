"""Criterio de aceptación de la Fase 4 (firma digital PAdES).

Con la pila real y sin red (TSA deshabilitada):
1. Genera un certificado PKCS#12 de prueba (por script).
2. Firma un PDF con sello visible.
3. Verifica con pyHanko usando el certificado como ancla de confianza -> VÁLIDA,
   firma íntegra que cubre todo el documento.
4. Demuestra que, tras firmar, un intento de edición se rechaza (DocumentoFirmado).
5. Crea una copia modificada tras la firma y verifica que se detecta -> INVÁLIDA.

Uso:
    uv run python scripts/verificar_firma_digital.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import fitz

from lectorpdf.adapters.pyhanko.signature_service import PyHankoSignatureService
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.estampado_service import PyMuPDFEstampadoService
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.errores import DocumentoFirmado
from lectorpdf.core.domain.firma_digital import (
    ConfigFirma,
    CredencialPKCS12,
    EstadoFirma,
)
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.use_cases.firmar_digitalmente import FirmarDigitalmente
from lectorpdf.core.use_cases.verificar_firmas import VerificarFirmas

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.adapters.certificado_prueba import generar_pkcs12  # noqa: E402


def _pdf(destino: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=420, height=300)
    page.insert_text((40, 60), "CONTRATO DE PRUEBA", fontsize=18)
    page.insert_text((40, 100), "El abajo firmante acepta las condiciones.", fontsize=11)
    doc.save(destino)
    doc.close()


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    p12, der = generar_pkcs12(tmp / "cert", contrasena="prueba")
    pdf = tmp / "contrato.pdf"
    _pdf(pdf)

    # --- Firmar (sello visible) ---
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(pdf)
    servicio = PyHankoSignatureService(registro)
    FirmarDigitalmente(servicio).ejecutar(
        documento,
        ConfigFirma(pagina=0, rect_pt=RectanguloPt(250, 210, 400, 270), razon="Conforme"),
        CredencialPKCS12(p12, "prueba"),
    )

    # --- Verificar el PDF firmado ---
    firmado = VerificarFirmas(servicio).ejecutar(documento, [der])

    # --- Intento de edición tras firmar (debe rechazarse) ---
    estampado = PyMuPDFEstampadoService(registro)
    try:
        estampado.estampar_imagen(documento.id, 0, RectanguloPt(0, 0, 10, 10), b"x")
        edicion_rechazada = False
    except DocumentoFirmado:
        edicion_rechazada = True
    registro.cerrar(documento.id)

    # --- Manipular tras la firma y verificar la copia ---
    manipulado = tmp / "contrato_manipulado.pdf"
    manipulado.write_bytes(pdf.read_bytes())
    doc = fitz.open(manipulado)
    doc[0].insert_text((40, 150), "CLAUSULA ANADIDA TRAS LA FIRMA", fontsize=12)
    doc.save(manipulado, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()

    registro2 = RegistroDocumentos()
    doc2 = PyMuPDFDocumentRepository(registro2).abrir(manipulado)
    manip = VerificarFirmas(PyHankoSignatureService(registro2)).ejecutar(doc2, [der])
    registro2.cerrar(doc2.id)

    # --- Informe ---
    print("-" * 66)
    print("PDF firmado:                 ", pdf)
    f = firmado[0]
    print(f"  Estado:                    {f.estado.name}")
    print(f"  Firmante:                  {f.firmante}")
    print(f"  Cubre todo el documento:   {f.cubre_todo_el_documento}")
    print(f"Edición tras firmar rechazada: {edicion_rechazada}")
    print("-" * 66)
    print("Copia modificada tras la firma:", manipulado)
    m = manip[0]
    print(f"  Estado:                    {m.estado.name}")
    print(f"  Cubre todo el documento:   {m.cubre_todo_el_documento}")
    print(f"  Motivo:                    {m.motivo}")
    print("-" * 66)

    ok = (
        f.estado == EstadoFirma.VALIDA
        and f.cubre_todo_el_documento
        and edicion_rechazada
        and m.estado == EstadoFirma.INVALIDA
        and not m.cubre_todo_el_documento
    )
    print("RESULTADO:", "OK" if ok else "FALLO")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
