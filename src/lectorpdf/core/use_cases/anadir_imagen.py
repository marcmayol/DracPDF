"""Caso de uso: insertar una imagen desde fichero en un rectángulo de una página."""

from __future__ import annotations

from lectorpdf.core.domain.anotaciones import ImagenNueva
from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_anotaciones import ServicioAnotaciones


class AnadirImagen:
    def __init__(self, servicio: ServicioAnotaciones) -> None:
        self._servicio = servicio

    def ejecutar(
        self, documento: Documento, pagina: int, imagen: ImagenNueva
    ) -> None:
        if pagina < 0 or pagina >= documento.num_paginas:
            raise PaginaFueraDeRango(
                f"Página {pagina} fuera de rango [0, {documento.num_paginas})"
            )
        if not imagen.ruta.is_file():
            raise ValueError(f"La imagen no existe: {imagen.ruta}")
        r = imagen.rect_pt
        if r.x1 <= r.x0 or r.y1 <= r.y0:
            raise ValueError("El rectángulo de la imagen es inválido")
        self._servicio.anadir_imagen(documento.id, pagina, imagen)
