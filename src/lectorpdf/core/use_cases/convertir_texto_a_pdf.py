"""Caso de uso: convertir Markdown, HTML, texto plano u ODT externo a PDF."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.conversion import EXTENSIONES_TEXTO, ConfigPagina
from lectorpdf.core.domain.errores import DocumentoNoEncontrado, ErrorDominio
from lectorpdf.core.domain.herramientas import Progreso
from lectorpdf.core.ports.conversor_texto import ConversorTexto


class ConvertirTextoAPdf:
    def __init__(self, conversor: ConversorTexto) -> None:
        self._conversor = conversor

    def ejecutar(
        self,
        ruta: Path,
        destino: Path,
        config: ConfigPagina | None = None,
        progreso: Progreso | None = None,
    ) -> None:
        if not ruta.exists() or not ruta.is_file():
            raise DocumentoNoEncontrado(f"No existe el fichero: {ruta}")
        if ruta.suffix.lower() not in EXTENSIONES_TEXTO:
            raise ErrorDominio(
                f"No es Markdown, HTML, texto plano ni ODT: {ruta.name}"
            )
        self._conversor.a_pdf(ruta, destino, config or ConfigPagina(), progreso)
