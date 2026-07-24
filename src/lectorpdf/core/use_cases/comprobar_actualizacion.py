"""Caso de uso: comprobar si hay una versión más nueva que la instalada.

Compara versiones SEMÁNTICAMENTE (packaging.version), nunca por strings: un
manifiesto con versión menor o igual que la instalada es "al día", jamás se
ofrece bajar. Tolerancia total a fallos: cualquier excepción del puerto (red,
DNS, JSON malformado, HTTP 5xx, versión inválida) se convierte en un resultado
``ERROR`` de dominio; nunca se propaga.
"""

from __future__ import annotations

from packaging.version import Version

from lectorpdf.core.domain.actualizacion import (
    ResultadoComprobacion,
    TipoResultado,
)
from lectorpdf.core.ports.actualizador_service import ActualizadorService


class ComprobarActualizacion:
    def __init__(self, servicio: ActualizadorService) -> None:
        self._servicio = servicio

    def ejecutar(
        self, version_actual: str, etag: str | None = None
    ) -> ResultadoComprobacion:
        try:
            manifiesto, nuevo_etag = self._servicio.descargar_manifiesto(etag)
            if manifiesto is None:  # 304: ETag sin cambios
                return ResultadoComprobacion(TipoResultado.SIN_CAMBIOS_ETAG, etag=etag)
            if Version(manifiesto.version) <= Version(version_actual):
                # Se conserva el manifiesto (aunque no haya novedad) para que la
                # UI conozca check_horas y programe la comprobación periódica.
                return ResultadoComprobacion(
                    TipoResultado.AL_DIA, manifiesto=manifiesto, etag=nuevo_etag
                )
            return ResultadoComprobacion(
                TipoResultado.HAY_ACTUALIZACION,
                manifiesto=manifiesto,
                etag=nuevo_etag,
            )
        except Exception as exc:  # tolerancia absoluta: jamás propagar
            return ResultadoComprobacion(TipoResultado.ERROR, error=str(exc))
