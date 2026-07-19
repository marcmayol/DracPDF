"""Caso de uso: listar los campos de formulario de un documento."""

from __future__ import annotations

from lectorpdf.core.domain.errores import FormularioXFANoSoportado
from lectorpdf.core.domain.formularios import CampoFormulario
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.form_service import FormService


class ListarCampos:
    def __init__(self, servicio: FormService) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento) -> tuple[CampoFormulario, ...]:
        if self._servicio.es_xfa(documento.id):
            raise FormularioXFANoSoportado(
                "El documento usa formularios XFA, no soportados."
            )
        return self._servicio.listar_campos(documento.id)
