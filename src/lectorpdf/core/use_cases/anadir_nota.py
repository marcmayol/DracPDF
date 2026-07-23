"""Caso de uso: añadir una nota adhesiva en un punto de una página."""

from __future__ import annotations

from lectorpdf.core.domain.anotaciones import Nota
from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_anotaciones import ServicioAnotaciones


class AnadirNota:
    def __init__(self, servicio: ServicioAnotaciones) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento, pagina: int, nota: Nota) -> None:
        if pagina < 0 or pagina >= documento.num_paginas:
            raise PaginaFueraDeRango(
                f"Página {pagina} fuera de rango [0, {documento.num_paginas})"
            )
        if not nota.texto.strip():
            raise ValueError("La nota está vacía")
        self._servicio.anadir_nota(documento.id, pagina, nota)
