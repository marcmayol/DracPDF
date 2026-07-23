"""Caso de uso: eliminar una anotación (por su xref) de una página."""

from __future__ import annotations

from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_anotaciones import ServicioAnotaciones


class EliminarAnotacion:
    def __init__(self, servicio: ServicioAnotaciones) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento, pagina: int, xref: int) -> None:
        if pagina < 0 or pagina >= documento.num_paginas:
            raise PaginaFueraDeRango(
                f"Página {pagina} fuera de rango [0, {documento.num_paginas})"
            )
        self._servicio.eliminar_anotacion(documento.id, pagina, xref)
