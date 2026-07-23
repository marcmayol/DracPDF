"""Criterio de aceptación funcional de la Fase 9 (texto, anotaciones, imágenes).

Sin UI, sobre fixtures generados por script. Verifica, con exit 0:

  1. Texto añadido persiste tras guardar/reabrir con la fuente embebida (Type0).
  2. Anotaciones estándar (resaltar/subrayar/tachar y nota) creadas; una eliminada.
  3. Corrección: el texto original NO es extraíble tras corregir, y el caso
     "no cabe" ofrece alternativas (lanza TextoNoCabe con reducir=False; con
     reducir=True encaja).
  4. Imagen añadida y otra eliminada, verificadas TRAS reabrir; con el aviso de
     imagen en varias páginas.

Uso:
    uv run python scripts/verificar_anotaciones.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # consola cp1252 → utf-8
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.adapters.generar_fixtures import (  # noqa: E402
    generar_pdf_con_imagenes,
    generar_pdf_contenido,
    generar_pdf_parrafos,
)

from lectorpdf.adapters.pymupdf.anotaciones import PyMuPDFAnotaciones  # noqa: E402
from lectorpdf.adapters.pymupdf.document_repository import (  # noqa: E402
    PyMuPDFDocumentRepository,
)
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos  # noqa: E402
from lectorpdf.core.domain.anotaciones import (  # noqa: E402
    Correccion,
    FuenteTexto,
    ImagenNueva,
    Nota,
    TextoNuevo,
    TipoMarcado,
)
from lectorpdf.core.domain.errores import TextoNoCabe  # noqa: E402
from lectorpdf.core.domain.formularios import RectanguloPt  # noqa: E402

_resultados: list[tuple[str, bool]] = []


def _check(nombre: str, condicion: bool) -> None:
    _resultados.append((nombre, condicion))


def _texto(page: fitz.Page) -> str:
    return page.get_text().replace("\xa0", " ")


def _fuente_embebida(page: fitz.Page) -> bool:
    return any(f[2] == "Type0" and f[1] == "ttf" for f in page.get_fonts(full=True))


def _color_centro(page: fitz.Page, rect_pt: RectanguloPt) -> tuple[int, int, int]:
    r = fitz.Rect(rect_pt.x0, rect_pt.y0, rect_pt.x1, rect_pt.y1) + (2, 2, -2, -2)
    pix = page.get_pixmap(clip=r, dpi=72)
    return pix.pixel(pix.width // 2, pix.height // 2)


def _abrir(registro: RegistroDocumentos, ruta: Path) -> str:
    return PyMuPDFDocumentRepository(registro).abrir(ruta).id


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    registro = RegistroDocumentos()
    servicio = PyMuPDFAnotaciones(registro)

    # 1. Texto añadido con fuente embebida, persistente tras reabrir. ----------
    doc_id = _abrir(registro, generar_pdf_contenido(tmp / "contenido.pdf"))
    servicio.anadir_texto(
        doc_id,
        0,
        TextoNuevo(
            RectanguloPt(72, 300, 500, 340),
            "Anotación embebida áéí",
            FuenteTexto.SANS,
            14.0,
            (0.1, 0.1, 0.1),
        ),
    )
    salida = tmp / "con_texto.pdf"
    registro.obtener(doc_id).save(str(salida))
    registro.cerrar(doc_id)
    reab = fitz.open(salida)
    _check(
        "Texto añadido persiste con fuente embebida (Type0)",
        "Anotación embebida" in _texto(reab[0]) and _fuente_embebida(reab[0]),
    )
    reab.close()

    # 2. Anotaciones estándar creadas y una eliminada. -------------------------
    doc_id = _abrir(registro, generar_pdf_contenido(tmp / "c2.pdf"))
    rect = RectanguloPt(72, 66, 300, 82)
    servicio.marcar(doc_id, 0, (rect,), TipoMarcado.RESALTADO, (1.0, 0.9, 0.2))
    servicio.marcar(doc_id, 0, (rect,), TipoMarcado.SUBRAYADO, (0.2, 0.4, 0.9))
    servicio.anadir_nota(doc_id, 0, Nota(120.0, 200.0, "Revisar"))
    creadas = len(list(registro.obtener(doc_id)[0].annots()))
    xref = servicio.anotacion_en(doc_id, 0, 120.0, 200.0)
    assert xref is not None
    servicio.eliminar_anotacion(doc_id, 0, xref)
    tras = len(list(registro.obtener(doc_id)[0].annots()))
    _check("Anotaciones estándar creadas (3) y una eliminada", creadas == 3 and tras == 2)
    registro.cerrar(doc_id)

    # 3. Corrección: original no extraíble + caso "no cabe". -------------------
    doc_id = _abrir(registro, generar_pdf_parrafos(tmp / "parrafos.pdf"))
    r = registro.obtener(doc_id)[0].search_for("CINCUENTA")[0]
    servicio.corregir_texto(
        doc_id,
        0,
        Correccion(
            RectanguloPt(r.x0, r.y0, r.x1, r.y1),
            "OCHENTA",
            FuenteTexto.SERIF,
            (0.0, 0.0, 0.0),
        ),
    )
    salida = tmp / "corregido.pdf"
    registro.obtener(doc_id).save(str(salida))
    registro.cerrar(doc_id)
    reab = fitz.open(salida)
    _check(
        "Corrección: original no extraíble y sustituto presente",
        "CINCUENTA" not in _texto(reab[0]) and "OCHENTA" in _texto(reab[0]),
    )
    reab.close()

    # "No cabe": un texto largo en el hueco corto "OK" (tamaño 22).
    doc_id = _abrir(registro, generar_pdf_parrafos(tmp / "p2.pdf"))
    rok = registro.obtener(doc_id)[0].search_for("OK")[0]
    hueco = RectanguloPt(rok.x0, rok.y0, rok.x1, rok.y1)
    largo = "PALABRA DEMASIADO LARGA"
    ofrece_alternativa = False
    try:
        servicio.corregir_texto(
            doc_id, 0, Correccion(hueco, largo, FuenteTexto.SANS, (0, 0, 0))
        )
    except TextoNoCabe:
        # Se ofrece reducir: con reducir=True, encaja sin invadir al vecino.
        servicio.corregir_texto(
            doc_id,
            0,
            Correccion(hueco, largo, FuenteTexto.SANS, (0, 0, 0), reducir=True),
        )
        ofrece_alternativa = largo in _texto(registro.obtener(doc_id)[0])
    _check('Caso "no cabe" ofrece reducir y encaja', ofrece_alternativa)
    registro.cerrar(doc_id)

    # 4. Imagen añadida y otra eliminada, verificadas tras reabrir. ------------
    doc_id = _abrir(registro, generar_pdf_con_imagenes(tmp / "imgs.pdf"))
    # 4a. Añadir un logo nuevo en la página 0.
    png = tmp / "verde.png"
    pm = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 24, 24), False)
    pm.set_rect(pm.irect, (30, 180, 60))
    pm.save(str(png))
    rect_nueva = RectanguloPt(200, 200, 260, 260)
    servicio.anadir_imagen(doc_id, 0, ImagenNueva(rect_nueva, png))
    # 4b. Eliminar la imagen compartida (avisa: en varias páginas).
    compartida = servicio.imagenes_en(doc_id, 0)[0]
    aviso_multipagina = compartida.en_varias_paginas
    servicio.eliminar_imagen(doc_id, 0, compartida)
    salida = tmp / "img_final.pdf"
    registro.obtener(doc_id).save(str(salida))
    registro.cerrar(doc_id)
    reab = fitz.open(salida)
    anadida_ok = _color_centro(reab[0], rect_nueva) == (30, 180, 60)
    borrada_ok = _color_centro(reab[0], compartida.rect_pt) == (255, 255, 255)
    reab.close()
    _check("Imagen añadida verificada tras reabrir", anadida_ok)
    _check("Imagen eliminada verificada tras reabrir", borrada_ok)
    _check("Aviso: imagen usada en varias páginas", aviso_multipagina)

    print("-" * 62)
    ok = True
    for nombre, cond in _resultados:
        print(f"  [{'OK' if cond else 'FALLO'}] {nombre}")
        ok = ok and cond
    print("-" * 62)
    print("PyMuPDF:", fitz.VersionBind, "(sin downgrade; el proyecto fija >=1.24)")
    print("RESULTADO:", "OK" if ok else "FALLO")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
