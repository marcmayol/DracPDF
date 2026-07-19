"""Caso de uso: proteger con contraseña (cifrar) el documento abierto."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_herramientas import ServicioHerramientas


class ProtegerPdf:
    def __init__(self, servicio: ServicioHerramientas) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento, destino: Path, contrasena: str) -> None:
        if not contrasena:
            raise ValueError("La contraseña no puede estar vacía")
        self._servicio.proteger(documento.id, destino, contrasena)
