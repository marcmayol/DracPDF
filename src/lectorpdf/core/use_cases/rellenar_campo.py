"""Caso de uso: rellenar (escribir) el valor de un campo de formulario."""

from __future__ import annotations

from lectorpdf.core.domain.errores import CampoSoloLectura, ValorDeCampoInvalido
from lectorpdf.core.domain.formularios import CampoFormulario, TipoCampo
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.form_service import FormService

_ESTADO_OFF = "Off"


class RellenarCampo:
    def __init__(self, servicio: FormService) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento, campo: CampoFormulario, valor: str) -> None:
        if campo.solo_lectura:
            raise CampoSoloLectura(campo.id)
        self._validar_valor(campo, valor)
        self._servicio.escribir_valor(documento.id, campo.id, valor)

    def _validar_valor(self, campo: CampoFormulario, valor: str) -> None:
        if campo.tipo in (TipoCampo.COMBO, TipoCampo.LISTA, TipoCampo.RADIO):
            if valor not in campo.opciones:
                raise ValorDeCampoInvalido(
                    f"{valor!r} no está entre las opciones de {campo.nombre}"
                )
        elif campo.tipo == TipoCampo.CASILLA:
            permitidos = {_ESTADO_OFF, campo.estado_activado}
            if valor not in permitidos:
                raise ValorDeCampoInvalido(
                    f"{valor!r} no es un estado válido de la casilla {campo.nombre}"
                )
