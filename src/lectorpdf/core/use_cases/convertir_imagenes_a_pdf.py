"""Caso de uso: convertir imágenes externas en un PDF, una por página."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from lectorpdf.core.domain.conversion import (
    EXTENSIONES_IMAGEN,
    AjusteImagen,
    ConfigPagina,
)
from lectorpdf.core.domain.errores import DocumentoNoEncontrado, ErrorDominio
from lectorpdf.core.domain.herramientas import Progreso
from lectorpdf.core.ports.conversor_imagenes import ConversorImagenes


class ConvertirImagenesAPdf:
    """El orden de `rutas` es el orden de las páginas: lo decide quien llama."""

    def __init__(self, conversor: ConversorImagenes) -> None:
        self._conversor = conversor

    def ejecutar(
        self,
        rutas: Sequence[Path],
        destino: Path,
        ajuste: AjusteImagen = AjusteImagen.TAMANO_IMAGEN,
        config: ConfigPagina | None = None,
        progreso: Progreso | None = None,
    ) -> None:
        if not rutas:
            raise ErrorDominio("No hay ninguna imagen que convertir")
        for ruta in rutas:
            if not ruta.exists() or not ruta.is_file():
                raise DocumentoNoEncontrado(f"No existe el fichero: {ruta}")
            if ruta.suffix.lower() not in EXTENSIONES_IMAGEN:
                raise ErrorDominio(f"No es una imagen admitida: {ruta.name}")
        self._conversor.a_pdf(
            rutas, destino, ajuste, config or ConfigPagina(), progreso
        )
