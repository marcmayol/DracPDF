"""Caso de uso: obtener las propiedades del documento abierto."""

from __future__ import annotations

from lectorpdf.core.domain.contenido import PropiedadesDocumento
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.servicio_propiedades import ServicioPropiedades


class ObtenerPropiedades:
    def __init__(self, servicio: ServicioPropiedades) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento) -> PropiedadesDocumento:
        return self._servicio.propiedades(documento.id)
