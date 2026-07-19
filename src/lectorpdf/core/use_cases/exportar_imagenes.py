"""Caso de uso: exportar el documento abierto a imágenes PNG (una por página)."""

from __future__ import annotations

from pathlib import Path

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
        progreso: Progreso | None = None,
    ) -> list[Path]:
        if dpi <= 0:
            raise ValueError("El DPI debe ser positivo")
        return self._servicio.exportar_png(documento.id, directorio, dpi, progreso)
