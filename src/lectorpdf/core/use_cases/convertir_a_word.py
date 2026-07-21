"""Caso de uso: convertir el documento abierto a Word (.docx)."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.herramientas import Progreso, Rango
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.conversor_pdf import ConversorPDF


class ConvertirAWord:
    def __init__(self, conversor: ConversorPDF) -> None:
        self._conversor = conversor

    def ejecutar(
        self,
        documento: Documento,
        destino: Path,
        rango: Rango | None = None,
        progreso: Progreso | None = None,
    ) -> None:
        self._conversor.a_word(documento.id, destino, rango, progreso)
