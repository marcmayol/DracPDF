"""Caso de uso: deshacer/rehacer ediciones de formulario del documento abierto."""

from __future__ import annotations

from lectorpdf.core.domain.formularios import CambioValor
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.form_service import FormService


class HistorialFormulario:
    def __init__(self, servicio: FormService) -> None:
        self._servicio = servicio

    def puede_deshacer(self, documento: Documento) -> bool:
        return self._servicio.puede_deshacer(documento.id)

    def puede_rehacer(self, documento: Documento) -> bool:
        return self._servicio.puede_rehacer(documento.id)

    def deshacer(self, documento: Documento) -> CambioValor | None:
        return self._servicio.deshacer(documento.id)

    def rehacer(self, documento: Documento) -> CambioValor | None:
        return self._servicio.rehacer(documento.id)
