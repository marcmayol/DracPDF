"""Puerto de firma digital y verificación (PAdES).

Opera por `documento_id`: el adaptador obtiene los bytes/rutas del registro
compartido, nunca del caso de uso. La credencial es un concepto de dominio.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.firma_digital import (
    ConfigFirma,
    CredencialFirma,
    ResultadoVerificacion,
)


@runtime_checkable
class SignatureService(Protocol):
    def firmar(
        self,
        documento_id: str,
        config: ConfigFirma,
        credencial: CredencialFirma,
    ) -> None:
        """Firma el documento (guardando antes los cambios pendientes) y lo deja
        marcado como firmado. La firma es una revisión incremental final."""
        ...

    def verificar(
        self,
        documento_id: str,
        anclas_confianza: Sequence[Path],
    ) -> tuple[ResultadoVerificacion, ...]:
        """Verifica las firmas del documento contra las anclas de confianza."""
        ...
