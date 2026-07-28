"""Caso de uso: convertir las páginas del documento abierto a imágenes.

Una imagen por página, salvo en TIFF, que las reúne todas en un solo fichero.
"""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.conversion import CALIDAD_POR_DEFECTO, FormatoImagen
from lectorpdf.core.domain.herramientas import Progreso
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_herramientas import ServicioHerramientas

DPI_POR_DEFECTO = 150


class ExportarImagenes:
    def __init__(self, servicio: ServicioHerramientas) -> None:
        self._servicio = servicio

    def ejecutar(
        self,
        documento: Documento,
        directorio: Path,
        dpi: int = DPI_POR_DEFECTO,
        formato: FormatoImagen = FormatoImagen.PNG,
        calidad: int = CALIDAD_POR_DEFECTO,
        progreso: Progreso | None = None,
    ) -> list[Path]:
        if dpi <= 0:
            raise ValueError("El DPI debe ser positivo")
        if not 1 <= calidad <= 100:
            raise ValueError("La calidad debe estar entre 1 y 100")
        return self._servicio.exportar_imagenes(
            documento.id, directorio, dpi, formato, calidad, progreso
        )
