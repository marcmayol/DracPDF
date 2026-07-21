"""Caso de uso: convertir el documento abierto a HTML."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.herramientas import Progreso, Rango
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.conversor_pdf import ConversorPDF


class ConvertirAHtml:
    def __init__(self, conversor: ConversorPDF) -> None:
        self._conversor = conversor

    def ejecutar(
        self,
        documento: Documento,
        destino: Path,
        rango: Rango | None = None,
        imagenes_embebidas: bool = True,
        progreso: Progreso | None = None,
    ) -> None:
        self._conversor.a_html(
            documento.id, destino, rango, imagenes_embebidas, progreso
        )
