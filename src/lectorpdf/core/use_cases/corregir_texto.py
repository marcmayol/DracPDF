"""Caso de uso: corregir (sustituir) un tramo de una línea de texto existente."""

from __future__ import annotations

from lectorpdf.core.domain.anotaciones import Correccion, FuenteTexto
from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_anotaciones import ServicioAnotaciones


class CorregirTexto:
    def __init__(self, servicio: ServicioAnotaciones) -> None:
        self._servicio = servicio

    def cabe(
        self,
        documento: Documento,
        pagina: int,
        rect_pt: RectanguloPt,
        texto: str,
        fuente: FuenteTexto,
    ) -> bool:
        return self._servicio.cabe_texto(documento.id, pagina, rect_pt, texto, fuente)

    def ejecutar(
        self, documento: Documento, pagina: int, correccion: Correccion
    ) -> None:
        if pagina < 0 or pagina >= documento.num_paginas:
            raise PaginaFueraDeRango(
                f"Página {pagina} fuera de rango [0, {documento.num_paginas})"
            )
        if not correccion.texto_nuevo.strip():
            raise ValueError("El texto de sustitución está vacío")
        self._servicio.corregir_texto(documento.id, pagina, correccion)
