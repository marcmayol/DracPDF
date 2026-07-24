"""Modelos de dominio del sistema de actualizaciones (Fase 10).

El core no conoce red ni Qt: solo describe el manifiesto y el resultado de la
comprobación como valores. La app instalada solo conoce la URL del manifiesto;
nunca la API de GitHub.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Manifiesto:
    """Contenido de ``updates.json``. Los campos de extensión (``canal``,
    ``porcentaje_despliegue``) se declaran pero no se usan todavía."""

    version: str
    url: str
    sha256: str
    notas: str
    check_horas: int
    canal: str | None = None
    porcentaje_despliegue: int | None = None


class TipoResultado(Enum):
    HAY_ACTUALIZACION = "hay_actualizacion"
    AL_DIA = "al_dia"
    SIN_CAMBIOS_ETAG = "sin_cambios_etag"  # 304 Not Modified
    ERROR = "error"


@dataclass(frozen=True)
class ResultadoComprobacion:
    """Resultado de comprobar actualizaciones, como valor de dominio.

    - ``HAY_ACTUALIZACION``: ``manifiesto`` presente.
    - ``AL_DIA`` / ``SIN_CAMBIOS_ETAG``: sin novedad.
    - ``ERROR``: ``error`` con el motivo (la comprobación manual lo muestra; la
      automática lo ignora en silencio).

    ``etag`` lleva el nuevo ETag para que la UI lo persista y lo reutilice.
    """

    tipo: TipoResultado
    manifiesto: Manifiesto | None = None
    etag: str | None = None
    error: str | None = None

    @property
    def hay_actualizacion(self) -> bool:
        return self.tipo is TipoResultado.HAY_ACTUALIZACION
