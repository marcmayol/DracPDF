"""Caso de uso: quitar la protección (contraseña) de un PDF (por ruta)."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.errores import DocumentoNoEncontrado
from lectorpdf.core.ports.servicio_herramientas import ServicioHerramientas


class DesprotegerPdf:
    def __init__(self, servicio: ServicioHerramientas) -> None:
        self._servicio = servicio

    def ejecutar(self, ruta: Path, contrasena: str, destino: Path) -> None:
        if not ruta.is_file():
            raise DocumentoNoEncontrado(f"No existe el fichero: {ruta}")
        self._servicio.desproteger(ruta, contrasena, destino)
