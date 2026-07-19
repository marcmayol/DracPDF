"""Criterio de aceptación de la Fase 6 (herramientas de PDF).

Con la pila real (casos de uso + adaptador PyMuPDF), ejecuta el ciclo completo:
unir (comprobando el orden), dividir, proteger y reabrir con contraseña,
desproteger (comprobando la igualdad de contenido), comprimir (reportando la
reducción) y exportar a PNG y texto. Además demuestra que organizar páginas de un
documento FIRMADO se rechaza.

Uso:
    uv run python scripts/verificar_herramientas.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import fitz

from lectorpdf.adapters.pyhanko.signature_service import PyHankoSignatureService
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.herramientas import PyMuPDFHerramientas
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.errores import DocumentoFirmado
from lectorpdf.core.domain.firma_digital import ConfigFirma, CredencialPKCS12
from lectorpdf.core.domain.herramientas import Rango
from lectorpdf.core.use_cases.comprimir_pdf import ComprimirPdf
from lectorpdf.core.use_cases.desproteger_pdf import DesprotegerPdf
from lectorpdf.core.use_cases.dividir_pdf import DividirPdf
from lectorpdf.core.use_cases.exportar_imagenes import ExportarImagenes
from lectorpdf.core.use_cases.exportar_texto import ExportarTexto
from lectorpdf.core.use_cases.organizar_paginas import OrganizarPaginas
from lectorpdf.core.use_cases.proteger_pdf import ProtegerPdf
from lectorpdf.core.use_cases.unir_pdf import UnirPdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.adapters.certificado_prueba import generar_pkcs12  # noqa: E402


def _pdf(ruta: Path, textos: list[str]) -> Path:
    doc = fitz.open()
    for texto in textos:
        doc.new_page(width=300, height=400).insert_text((40, 60), texto, fontsize=14)
    doc.save(ruta)
    doc.close()
    return ruta


def _texto(ruta: Path) -> str:
    doc = fitz.open(ruta)
    texto = "".join(p.get_text() for p in doc)
    doc.close()
    return texto


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    registro = RegistroDocumentos()
    repo = PyMuPDFDocumentRepository(registro)
    herr = PyMuPDFHerramientas(registro)
    resultados: list[tuple[str, bool, str]] = []

    # 1) UNIR (orden b -> a).
    a = _pdf(tmp / "a.pdf", ["A1", "A2"])
    b = _pdf(tmp / "b.pdf", ["B1"])
    unido = tmp / "unido.pdf"
    UnirPdf(herr).ejecutar([b, a], unido)
    d = fitz.open(unido)
    orden_ok = d.page_count == 3 and d[0].get_text().strip() == "B1"
    d.close()
    resultados.append(("unir (orden b,a)", orden_ok, "3 págs, empieza por B1"))

    documento = repo.abrir(unido)
    texto_original = _texto(unido)

    # 2) DIVIDIR por rangos.
    partes = DividirPdf(herr).por_rangos(
        documento, [Rango(1, 2), Rango(3, 3)], tmp / "partes"
    )
    dividir_ok = len(partes) == 2 and all(p.is_file() for p in partes)
    resultados.append(("dividir (2 rangos)", dividir_ok, f"{len(partes)} ficheros"))

    # 3) PROTEGER + reabrir con contraseña.
    prot = tmp / "prot.pdf"
    ProtegerPdf(herr).ejecutar(documento, prot, "clave")
    dp = fitz.open(prot)
    proteger_ok = bool(dp.needs_pass) and bool(dp.authenticate("clave"))
    dp.close()
    resultados.append(("proteger + reabrir", proteger_ok, "pide clave y abre"))

    # 4) DESPROTEGER (igualdad de contenido).
    desp = tmp / "desp.pdf"
    DesprotegerPdf(herr).ejecutar(prot, "clave", desp)
    dd = fitz.open(desp)
    desproteger_ok = not dd.needs_pass and _texto(desp) == texto_original
    dd.close()
    resultados.append(("desproteger (igualdad)", desproteger_ok, "sin clave; texto == original"))

    # 5) COMPRIMIR (reducción).
    comp = tmp / "comp.pdf"
    rc = ComprimirPdf(herr).ejecutar(documento, comp)
    comprimir_ok = comp.is_file() and rc.bytes_despues <= rc.bytes_antes
    detalle_comp = (
        f"{rc.bytes_antes} -> {rc.bytes_despues} B ({rc.porcentaje_reduccion:.1f}% menos)"
    )
    resultados.append(("comprimir", comprimir_ok, detalle_comp))

    # 6) EXPORTAR PNG + texto.
    pngs = ExportarImagenes(herr).ejecutar(documento, tmp / "imgs", dpi=100)
    txt = tmp / "texto.txt"
    ExportarTexto(herr).ejecutar(documento, txt)
    exportar_ok = (
        len(pngs) == 3
        and all(p.is_file() for p in pngs)
        and txt.is_file()
        and "B1" in txt.read_text(encoding="utf-8")
    )
    resultados.append(("exportar PNG+texto", exportar_ok, f"{len(pngs)} PNG + texto"))

    registro.cerrar(documento.id)

    # 7) FIRMADO: organizar se rechaza.
    p12, _ = generar_pkcs12(tmp / "cert", contrasena="prueba")
    firmable = repo.abrir(_pdf(tmp / "firmable.pdf", ["X", "Y"]))
    PyHankoSignatureService(registro).firmar(
        firmable.id, ConfigFirma(pagina=0), CredencialPKCS12(p12, "prueba")
    )
    try:
        OrganizarPaginas(herr).rotar(firmable, 0, 90)
        firmado_ok = False
    except DocumentoFirmado:
        firmado_ok = True
    resultados.append(("firmado rechaza organizar", firmado_ok, "DocumentoFirmado"))
    registro.cerrar(firmable.id)

    # Informe.
    print("-" * 72)
    for nombre, ok, detalle in resultados:
        print(f"{'OK  ' if ok else 'FALLO'}  {nombre:<28} {detalle}")
    print("-" * 72)
    todo_ok = all(ok for _, ok, _ in resultados)
    print("RESULTADO:", "OK" if todo_ok else "FALLO")
    return 0 if todo_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
