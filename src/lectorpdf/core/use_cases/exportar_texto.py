"""Caso de uso: exportar el texto del documento abierto a un fichero."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_herramientas import ServicioHerramientas


class ExportarTexto:
    def __init__(self, servicio: ServicioHerramientas) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento, destino: Path) -> None:
        self._servicio.exportar_texto(documento.id, destino)
