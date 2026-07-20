"""Caso de uso: obtener las palabras de una página (para seleccionar y copiar)."""

from __future__ import annotations

from lectorpdf.core.domain.contenido import PalabraTexto
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_texto import ServicioTexto


class ObtenerPalabras:
    def __init__(self, servicio: ServicioTexto) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento, pagina: int) -> tuple[PalabraTexto, ...]:
        return self._servicio.palabras(documento.id, pagina)
