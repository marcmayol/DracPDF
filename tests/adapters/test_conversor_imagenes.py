"""Tests de integración del conversor imágenes → PDF (PyMuPDF).

Las imágenes de fixture se generan aquí con PyMuPDF: nada de binarios en el repo.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from lectorpdf.adapters.pymupdf.conversor_imagenes import ConversorImagenesFitz
from lectorpdf.core.domain.conversion import AjusteImagen, ConfigPagina
from lectorpdf.core.domain.errores import ErrorDominio

_MM_A_PT = 72.0 / 25.4


def _imagen(destino: Path, ancho: int, alto: int, formato: str = "png") -> Path:
    """Escribe una imagen del tamaño pedido (en píxeles) con algo dibujado."""
    doc = fitz.open()
    pagina = doc.new_page(width=ancho, height=alto)
    pagina.draw_rect(fitz.Rect(0, 0, ancho, alto), color=(0.9, 0.2, 0.2), fill=(1, 1, 1))
    pagina.insert_text((10, alto / 2), f"{ancho}x{alto}", fontsize=12)
    pix = pagina.get_pixmap(dpi=72)
    pix.save(str(destino), output=formato)
    doc.close()
    return destino


def test_una_pagina_por_imagen_en_orden(tmp_path: Path) -> None:
    rutas = [
        _imagen(tmp_path / "1.png", 200, 100),
        _imagen(tmp_path / "2.png", 100, 200),
        _imagen(tmp_path / "3.jpg", 150, 150, formato="jpg"),
    ]
    destino = tmp_path / "salida.pdf"

    ConversorImagenesFitz().a_pdf(
        rutas, destino, AjusteImagen.TAMANO_IMAGEN, ConfigPagina()
    )

    doc = fitz.open(destino)
    try:
        assert doc.page_count == 3
        # Cada página conserva la proporción de su imagen (apaisada, vertical, cuadrada).
        assert doc[0].rect.width > doc[0].rect.height
        assert doc[1].rect.width < doc[1].rect.height
        assert round(doc[2].rect.width) == round(doc[2].rect.height)
    finally:
        doc.close()


def test_pagina_fija_usa_el_tamano_configurado(tmp_path: Path) -> None:
    rutas = [_imagen(tmp_path / "a.png", 400, 100), _imagen(tmp_path / "b.png", 50, 300)]
    destino = tmp_path / "salida.pdf"
    config = ConfigPagina(ancho_mm=210.0, alto_mm=297.0, margen_mm=20.0)

    ConversorImagenesFitz().a_pdf(rutas, destino, AjusteImagen.PAGINA_FIJA, config)

    doc = fitz.open(destino)
    try:
        assert doc.page_count == 2
        for pagina in doc:
            assert round(pagina.rect.width) == round(210.0 * _MM_A_PT)
            assert round(pagina.rect.height) == round(297.0 * _MM_A_PT)
            # La imagen cae dentro de los márgenes, sin desbordar la página.
            bloques = pagina.get_image_info()
            assert bloques, "la imagen debe estar insertada"
            caja = fitz.Rect(bloques[0]["bbox"])
            assert caja.x0 >= 20.0 * _MM_A_PT - 1
            assert caja.x1 <= pagina.rect.width - 20.0 * _MM_A_PT + 1
    finally:
        doc.close()


def test_reporta_progreso_por_imagen(tmp_path: Path) -> None:
    rutas = [_imagen(tmp_path / f"{i}.png", 80, 80) for i in range(4)]
    avances: list[tuple[int, int]] = []

    ConversorImagenesFitz().a_pdf(
        rutas,
        tmp_path / "s.pdf",
        AjusteImagen.TAMANO_IMAGEN,
        ConfigPagina(),
        lambda hecho, total: avances.append((hecho, total)),
    )

    assert avances == [(1, 4), (2, 4), (3, 4), (4, 4)]


def test_fichero_ilegible_no_deja_pdf_a_medias(tmp_path: Path) -> None:
    buena = _imagen(tmp_path / "buena.png", 100, 100)
    rota = tmp_path / "rota.png"
    rota.write_bytes(b"esto no es un PNG")
    destino = tmp_path / "salida.pdf"

    with pytest.raises(ErrorDominio):
        ConversorImagenesFitz().a_pdf(
            [buena, rota], destino, AjusteImagen.TAMANO_IMAGEN, ConfigPagina()
        )

    assert not destino.exists()  # escritura atómica: o el PDF entero, o nada
    assert not destino.with_name(destino.name + ".tmp").exists()
