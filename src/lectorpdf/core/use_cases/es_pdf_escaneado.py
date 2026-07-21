"""Caso de uso: detectar si el documento abierto es un PDF escaneado (sin texto)."""

from __future__ import annotations

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.conversor_pdf import ConversorPDF


class EsPdfEscaneado:
    def __init__(self, conversor: ConversorPDF) -> None:
        self._conversor = conversor

    def ejecutar(self, documento: Documento) -> bool:
        return self._conversor.es_escaneado(documento.id)
