"""Modelos de dominio para la Fase 9: texto, anotaciones e imágenes.

El core no conoce PyMuPDF ni Qt: solo describe QUÉ operación se pide (rectángulo
en puntos PDF, texto, fuente lógica, color…). Los adaptadores la ejecutan.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from lectorpdf.core.domain.formularios import RectanguloPt


class FuenteTexto(Enum):
    """Familias embebidas (OFL) disponibles para el texto nuevo."""

    SERIF = "serif"
    SANS = "sans"
    MONO = "mono"


class TipoMarcado(Enum):
    """Anotaciones de marcado sobre texto existente."""

    RESALTADO = "resaltado"
    SUBRAYADO = "subrayado"
    TACHADO = "tachado"


# Color RGB normalizado (0..1), como usa PyMuPDF.
Color = tuple[float, float, float]


@dataclass(frozen=True)
class TextoNuevo:
    """Texto a estampar en un rectángulo de una página."""

    rect_pt: RectanguloPt
    texto: str
    fuente: FuenteTexto
    tamano: float
    color: Color


@dataclass(frozen=True)
class Nota:
    """Nota adhesiva (anotación de texto emergente) en un punto de la página."""

    x_pt: float
    y_pt: float
    texto: str


@dataclass(frozen=True)
class Correccion:
    """Sustitución acotada de un tramo de una línea: se redacta el original y se
    escribe `texto_nuevo` en su rectángulo con una fuente sustituta embebida."""

    rect_pt: RectanguloPt
    texto_nuevo: str
    fuente: FuenteTexto
    tamano: float
    color: Color


@dataclass(frozen=True)
class ImagenNueva:
    """Imagen (PNG/JPEG) a insertar en un rectángulo de una página."""

    rect_pt: RectanguloPt
    ruta: Path
    conservar_proporcion: bool = True


@dataclass(frozen=True)
class ImagenEnPagina:
    """Una imagen detectada en la página (para el modo eliminar)."""

    xref: int
    rect_pt: RectanguloPt
    ancho_px: int
    alto_px: int
    en_varias_paginas: bool
    cubre_pagina: bool
