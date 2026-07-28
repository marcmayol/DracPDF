"""Casos de uso: convertir el documento abierto a ODT y a RTF.

Ambos son "reformateados": conservan el contenido y la estructura deducida
(títulos, párrafos, negritas y tablas), no el diseño exacto del PDF.
"""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.herramientas import Progreso, Rango
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.conversor_pdf import ConversorPDF


class ConvertirAOdt:
    def __init__(self, conversor: ConversorPDF) -> None:
        self._conversor = conversor

    def ejecutar(
        self,
        documento: Documento,
        destino: Path,
        rango: Rango | None = None,
        progreso: Progreso | None = None,
    ) -> None:
        self._conversor.a_odt(documento.id, destino, rango, progreso)


class ConvertirARtf:
    def __init__(self, conversor: ConversorPDF) -> None:
        self._conversor = conversor

    def ejecutar(
        self,
        documento: Documento,
        destino: Path,
        rango: Rango | None = None,
        progreso: Progreso | None = None,
    ) -> None:
        self._conversor.a_rtf(documento.id, destino, rango, progreso)
