"""Caso de uso: detectar y eliminar imágenes de una página.

Expone la detección (para el modo de selección visual) y el borrado. La lógica de
avisos (imagen en varias páginas o que cubre la página) vive en el dato
`ImagenEnPagina` que devuelve la detección; la UI decide cómo comunicarlo.
"""

from __future__ import annotations

from lectorpdf.core.domain.anotaciones import ImagenEnPagina
from lectorpdf.core.domain.errores import PaginaFueraDeRango
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_anotaciones import ServicioAnotaciones


class EliminarImagen:
    def __init__(self, servicio: ServicioAnotaciones) -> None:
        self._servicio = servicio

    def _validar_pagina(self, documento: Documento, pagina: int) -> None:
        if pagina < 0 or pagina >= documento.num_paginas:
            raise PaginaFueraDeRango(
                f"Página {pagina} fuera de rango [0, {documento.num_paginas})"
            )

    def imagenes(
        self, documento: Documento, pagina: int
    ) -> tuple[ImagenEnPagina, ...]:
        self._validar_pagina(documento, pagina)
        return self._servicio.imagenes_en(documento.id, pagina)

    def imagen_en(
        self, documento: Documento, pagina: int, x_pt: float, y_pt: float
    ) -> ImagenEnPagina | None:
        self._validar_pagina(documento, pagina)
        return self._servicio.imagen_en(documento.id, pagina, x_pt, y_pt)

    def eliminar(
        self, documento: Documento, pagina: int, imagen: ImagenEnPagina
    ) -> None:
        self._validar_pagina(documento, pagina)
        self._servicio.eliminar_imagen(documento.id, pagina, imagen)
