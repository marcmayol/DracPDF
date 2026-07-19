"""Modelos de dominio. Sin dependencias de infraestructura (Qt/PyMuPDF/pyHanko)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pagina:
    """Metadatos de una página. Las dimensiones van en puntos PDF (1/72 pulgada)."""

    indice: int
    ancho_pt: float
    alto_pt: float


@dataclass(frozen=True)
class Documento:
    """Documento abierto. `id` es un identificador de sesión que asigna el adaptador."""

    id: str
    ruta: Path
    paginas: tuple[Pagina, ...]
    titulo: str | None = None

    @property
    def num_paginas(self) -> int:
        return len(self.paginas)


@dataclass(frozen=True)
class ImagenRenderizada:
    """Resultado de renderizar una página: píxeles RGBA sin comprimir.

    `datos` contiene ancho_px * alto_px * 4 bytes en orden RGBA, listos para
    construir un QImage en la UI sin decodificación intermedia.
    """

    ancho_px: int
    alto_px: int
    datos: bytes
    escala: float
