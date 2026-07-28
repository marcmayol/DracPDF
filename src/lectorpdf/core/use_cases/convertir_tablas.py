"""Casos de uso: detectar las tablas del documento y convertirlas."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.errores import ErrorDominio
from lectorpdf.core.domain.herramientas import Progreso
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.domain.tablas import (
    EstrategiaTablas,
    FormatoTabla,
    TablaDetectada,
)
from lectorpdf.core.ports.servicio_tablas import ServicioTablas


class DetectarTablas:
    """Enseña qué tablas hay y dónde, sin escribir nada."""

    def __init__(self, servicio: ServicioTablas) -> None:
        self._servicio = servicio

    def ejecutar(
        self,
        documento: Documento,
        estrategia: EstrategiaTablas = EstrategiaTablas.LINEAS,
        progreso: Progreso | None = None,
    ) -> tuple[TablaDetectada, ...]:
        return self._servicio.detectar_tablas(documento.id, estrategia, progreso)


class ConvertirTablas:
    def __init__(self, servicio: ServicioTablas) -> None:
        self._servicio = servicio

    def ejecutar(
        self,
        documento: Documento,
        directorio: Path,
        formato: FormatoTabla,
        estrategia: EstrategiaTablas = EstrategiaTablas.LINEAS,
        progreso: Progreso | None = None,
    ) -> list[Path]:
        rutas = self._servicio.exportar_tablas(
            documento.id, directorio, formato, estrategia, progreso
        )
        if not rutas:
            # Escribir un fichero vacío haría creer que la conversión funcionó.
            raise ErrorDominio(
                "No se ha detectado ninguna tabla en el documento: no se ha "
                "creado ningún fichero"
            )
        return rutas
