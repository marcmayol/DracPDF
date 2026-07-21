"""Caso de uso: convertir un .docx externo a PDF (reformateado)."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.conversion import ConfigPagina
from lectorpdf.core.domain.errores import ErrorDominio
from lectorpdf.core.domain.herramientas import Progreso
from lectorpdf.core.ports.conversor_word import ConversorWord


class ConvertirWordAPdf:
    def __init__(self, conversor: ConversorWord) -> None:
        self._conversor = conversor

    def ejecutar(
        self,
        ruta_docx: Path,
        destino: Path,
        config: ConfigPagina,
        progreso: Progreso | None = None,
    ) -> None:
        if ruta_docx.suffix.lower() != ".docx":
            raise ErrorDominio(f"No es un documento Word (.docx): {ruta_docx.name}")
        self._conversor.a_pdf(ruta_docx, destino, config, progreso)
