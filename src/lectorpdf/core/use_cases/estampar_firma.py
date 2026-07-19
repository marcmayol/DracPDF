"""Caso de uso: estampar una firma (imagen PNG) sobre una página."""

from __future__ import annotations

from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.estampado_service import EstampadoService


class EstamparFirma:
    def __init__(self, servicio: EstampadoService) -> None:
        self._servicio = servicio

    def ejecutar(
        self,
        documento: Documento,
        pagina: int,
        rect_pt: RectanguloPt,
        imagen_png: bytes,
    ) -> None:
        if pagina < 0 or pagina >= documento.num_paginas:
            raise PaginaFueraDeRango(
                f"Página {pagina} fuera de rango [0, {documento.num_paginas})"
            )
        if not imagen_png:
            raise ValueError("La imagen de la firma está vacía")
        self._servicio.estampar_imagen(documento.id, pagina, rect_pt, imagen_png)
