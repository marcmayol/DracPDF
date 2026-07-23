"""Caso de uso: crear una anotación de marcado sobre la selección de texto."""

from __future__ import annotations

from lectorpdf.core.domain.anotaciones import Color, TipoMarcado
from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_anotaciones import ServicioAnotaciones


class MarcarSeleccion:
    def __init__(self, servicio: ServicioAnotaciones) -> None:
        self._servicio = servicio

    def ejecutar(
        self,
        documento: Documento,
        pagina: int,
        rects_pt: tuple[RectanguloPt, ...],
        tipo: TipoMarcado,
        color: Color,
    ) -> None:
        if pagina < 0 or pagina >= documento.num_paginas:
            raise PaginaFueraDeRango(
                f"Página {pagina} fuera de rango [0, {documento.num_paginas})"
            )
        if not rects_pt:
            raise ValueError("No hay selección que marcar")
        self._servicio.marcar(documento.id, pagina, rects_pt, tipo, color)
