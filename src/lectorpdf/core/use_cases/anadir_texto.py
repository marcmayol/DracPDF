"""Caso de uso: estampar un texto nuevo en un rectángulo de una página."""

from __future__ import annotations

from lectorpdf.core.domain.anotaciones import TextoNuevo
from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_anotaciones import ServicioAnotaciones


class AnadirTexto:
    def __init__(self, servicio: ServicioAnotaciones) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento, pagina: int, texto: TextoNuevo) -> None:
        if pagina < 0 or pagina >= documento.num_paginas:
            raise PaginaFueraDeRango(
                f"Página {pagina} fuera de rango [0, {documento.num_paginas})"
            )
        if not texto.texto.strip():
            raise ValueError("El texto a añadir está vacío")
        if texto.tamano <= 0:
            raise ValueError("El tamaño de fuente debe ser positivo")
        self._servicio.anadir_texto(documento.id, pagina, texto)
