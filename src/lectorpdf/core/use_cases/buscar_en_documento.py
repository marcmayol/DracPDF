"""Caso de uso: buscar un término en el documento abierto."""

from __future__ import annotations

from lectorpdf.core.domain.contenido import Coincidencia
from lectorpdf.core.domain.herramientas import Progreso
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_busqueda import ServicioBusqueda


class BuscarEnDocumento:
    def __init__(self, servicio: ServicioBusqueda) -> None:
        self._servicio = servicio

    def ejecutar(
        self,
        documento: Documento,
        termino: str,
        coincidir_mayusculas: bool = False,
        progreso: Progreso | None = None,
    ) -> tuple[Coincidencia, ...]:
        if not termino:
            return ()
        return self._servicio.buscar(
            documento.id, termino, coincidir_mayusculas, progreso
        )
