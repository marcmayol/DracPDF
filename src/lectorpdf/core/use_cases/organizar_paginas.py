"""Caso de uso: organizar páginas del documento abierto (rotar/eliminar/mover).

Muta el documento a través del servicio (que rechaza si está FIRMADO) y devuelve
un `Documento` actualizado con la nueva lista de páginas.
"""

from __future__ import annotations

from dataclasses import replace

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_herramientas import ServicioHerramientas


class OrganizarPaginas:
    def __init__(self, servicio: ServicioHerramientas) -> None:
        self._servicio = servicio

    def rotar(self, documento: Documento, indice: int, grados: int) -> Documento:
        paginas = self._servicio.rotar_pagina(documento.id, indice, grados)
        return replace(documento, paginas=paginas)

    def eliminar(self, documento: Documento, indice: int) -> Documento:
        paginas = self._servicio.eliminar_pagina(documento.id, indice)
        return replace(documento, paginas=paginas)

    def mover(self, documento: Documento, origen: int, destino: int) -> Documento:
        paginas = self._servicio.mover_pagina(documento.id, origen, destino)
        return replace(documento, paginas=paginas)
