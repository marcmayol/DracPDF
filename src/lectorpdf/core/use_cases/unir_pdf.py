"""Caso de uso: unir varios PDF (rutas de ficheros cerrados) en uno nuevo."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from lectorpdf.core.domain.errores import DocumentoNoEncontrado
from lectorpdf.core.domain.herramientas import Progreso
from lectorpdf.core.ports.servicio_herramientas import ServicioHerramientas


class UnirPdf:
    def __init__(self, servicio: ServicioHerramientas) -> None:
        self._servicio = servicio

    def ejecutar(
        self,
        rutas: Sequence[Path],
        destino: Path,
        progreso: Progreso | None = None,
    ) -> None:
        if len(rutas) < 2:
            raise ValueError("Se necesitan al menos dos ficheros para unir")
        for ruta in rutas:
            if not ruta.is_file():
                raise DocumentoNoEncontrado(f"No existe el fichero: {ruta}")
        self._servicio.unir(rutas, destino, progreso)
