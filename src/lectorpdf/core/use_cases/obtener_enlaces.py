"""Caso de uso: obtener los enlaces de una página del documento abierto."""

from __future__ import annotations

from lectorpdf.core.domain.contenido import Enlace
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_enlaces import ServicioEnlaces


class ObtenerEnlaces:
    def __init__(self, servicio: ServicioEnlaces) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento, pagina: int) -> tuple[Enlace, ...]:
        return self._servicio.enlaces(documento.id, pagina)
