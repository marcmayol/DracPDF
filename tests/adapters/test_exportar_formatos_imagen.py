"""Tests de PDF → imágenes en todos los formatos de salida."""

from __future__ import annotations

from html import unescape
from pathlib import Path

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.herramientas import PyMuPDFHerramientas
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.conversion import FormatoImagen

#: Primeros bytes que identifican cada formato, para no fiarse de la extensión.
_FIRMAS: dict[FormatoImagen, bytes] = {
    FormatoImagen.PNG: b"\x89PNG\r\n\x1a\n",
    FormatoImagen.JPEG: b"\xff\xd8\xff",
    FormatoImagen.WEBP: b"RIFF",
    FormatoImagen.TIFF: b"II*\x00",
}


def _servicio(ruta: Path) -> tuple[PyMuPDFHerramientas, str]:
    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    return PyMuPDFHerramientas(registro), documento.id


def test_un_fichero_por_pagina_con_su_firma(pdf_simple: Path, tmp_path: Path) -> None:
    servicio, doc_id = _servicio(pdf_simple)

    for formato in (FormatoImagen.PNG, FormatoImagen.JPEG, FormatoImagen.WEBP):
        destino = tmp_path / formato.value
        rutas = servicio.exportar_imagenes(doc_id, destino, dpi=72, formato=formato)

        assert len(rutas) == 3  # el fixture tiene 3 páginas
        for ruta in rutas:
            assert ruta.suffix == formato.extension
            assert ruta.read_bytes().startswith(_FIRMAS[formato])


def test_tiff_reune_todas_las_paginas_en_un_fichero(
    pdf_simple: Path, tmp_path: Path
) -> None:
    servicio, doc_id = _servicio(pdf_simple)

    rutas = servicio.exportar_imagenes(
        doc_id, tmp_path, dpi=72, formato=FormatoImagen.TIFF
    )

    assert len(rutas) == 1
    assert rutas[0].read_bytes().startswith(_FIRMAS[FormatoImagen.TIFF])

    from PIL import Image

    with Image.open(rutas[0]) as imagen:
        assert imagen.n_frames == 3  # las tres páginas dentro del mismo fichero


def test_svg_es_vectorial_y_conserva_el_texto(pdf_simple: Path, tmp_path: Path) -> None:
    servicio, doc_id = _servicio(pdf_simple)

    rutas = servicio.exportar_imagenes(
        doc_id, tmp_path, dpi=72, formato=FormatoImagen.SVG
    )

    assert len(rutas) == 3
    contenido = rutas[0].read_text(encoding="utf-8")
    assert "<svg" in contenido
    # El texto viaja como <text>, no como trazos: sigue siendo editable. Los
    # acentos van escapados como entidades XML, de ahí el unescape.
    assert "<text" in contenido
    assert "Página 1" in unescape(contenido)


def test_la_calidad_del_jpeg_cambia_el_peso(pdf_simple: Path, tmp_path: Path) -> None:
    servicio, doc_id = _servicio(pdf_simple)

    altas = servicio.exportar_imagenes(
        doc_id, tmp_path / "alta", dpi=150, formato=FormatoImagen.JPEG, calidad=95
    )
    bajas = servicio.exportar_imagenes(
        doc_id, tmp_path / "baja", dpi=150, formato=FormatoImagen.JPEG, calidad=20
    )

    assert bajas[0].stat().st_size < altas[0].stat().st_size


def test_reporta_progreso_por_pagina(pdf_simple: Path, tmp_path: Path) -> None:
    servicio, doc_id = _servicio(pdf_simple)
    avances: list[tuple[int, int]] = []

    servicio.exportar_imagenes(
        doc_id,
        tmp_path,
        dpi=72,
        formato=FormatoImagen.PNG,
        progreso=lambda hecho, total: avances.append((hecho, total)),
    )

    assert avances == [(1, 3), (2, 3), (3, 3)]
