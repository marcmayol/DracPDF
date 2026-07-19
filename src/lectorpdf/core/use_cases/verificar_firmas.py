"""Caso de uso: verificar las firmas digitales de un documento."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from lectorpdf.core.domain.firma_digital import ResultadoVerificacion
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.signature_service import SignatureService


class VerificarFirmas:
    def __init__(self, servicio: SignatureService) -> None:
        self._servicio = servicio

    def ejecutar(
        self,
        documento: Documento,
        anclas_confianza: Sequence[Path] = (),
    ) -> tuple[ResultadoVerificacion, ...]:
        return self._servicio.verificar(documento.id, anclas_confianza)
