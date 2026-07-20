"""Caso de uso: obtener el índice (outline) del documento abierto."""

from __future__ import annotations

from lectorpdf.core.domain.contenido import EntradaIndice
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_indice import ServicioIndice


class ObtenerIndice:
    def __init__(self, servicio: ServicioIndice) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento) -> tuple[EntradaIndice, ...]:
        return self._servicio.indice(documento.id)
