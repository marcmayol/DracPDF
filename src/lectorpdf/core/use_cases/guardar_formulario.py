"""Caso de uso: guardar el formulario y consultar si hay cambios sin guardar."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.form_service import FormService


class GuardarFormulario:
    def __init__(self, servicio: FormService) -> None:
        self._servicio = servicio

    def ejecutar(self, documento: Documento, destino: Path | None = None) -> None:
        """Guarda: con `destino=None`, incremental sobre el propio fichero."""
        self._servicio.guardar_incremental(documento.id, destino)

    def hay_cambios_sin_guardar(self, documento: Documento) -> bool:
        return self._servicio.esta_sucio(documento.id)
