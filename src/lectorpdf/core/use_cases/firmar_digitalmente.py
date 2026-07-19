"""Caso de uso: firmar digitalmente el documento."""

from __future__ import annotations

from lectorpdf.core.domain.errores import CredencialInvalida, PaginaFueraDeRango
from lectorpdf.core.domain.firma_digital import (
    ConfigFirma,
    CredencialFirma,
    CredencialPKCS12,
)
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.ports.signature_service import SignatureService


class FirmarDigitalmente:
    def __init__(self, servicio: SignatureService) -> None:
        self._servicio = servicio

    def ejecutar(
        self,
        documento: Documento,
        config: ConfigFirma,
        credencial: CredencialFirma,
    ) -> None:
        if config.pagina < 0 or config.pagina >= documento.num_paginas:
            raise PaginaFueraDeRango(
                f"Página {config.pagina} fuera de rango [0, {documento.num_paginas})"
            )
        if isinstance(credencial, CredencialPKCS12) and not credencial.ruta.exists():
            raise CredencialInvalida(f"No existe el certificado: {credencial.ruta}")
        self._servicio.firmar(documento.id, config, credencial)
