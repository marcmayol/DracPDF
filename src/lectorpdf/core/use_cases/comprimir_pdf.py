"""Caso de uso: comprimir (reducir tamaño) el documento abierto."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.herramientas import Progreso, ResultadoCompresion
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_herramientas import ServicioHerramientas


class ComprimirPdf:
    def __init__(self, servicio: ServicioHerramientas) -> None:
        self._servicio = servicio

    def ejecutar(
        self, documento: Documento, destino: Path, progreso: Progreso | None = None
    ) -> ResultadoCompresion:
        return self._servicio.comprimir(documento.id, destino, progreso)
