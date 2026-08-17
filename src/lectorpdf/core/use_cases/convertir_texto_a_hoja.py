"""Caso de uso: volcar todo el texto del documento a Excel o CSV.

El hermano simple de `ConvertirTablas`: no hay nada que detectar ni que elegir,
así que tampoco hay nada que preguntar. Lo que salga se parece al documento
línea a línea.
"""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.errores import ErrorDominio
from lectorpdf.core.domain.herramientas import Progreso
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.domain.tablas import FormatoTabla
from lectorpdf.core.ports.servicio_tablas import ServicioTablas


class ConvertirTextoAHoja:
    def __init__(self, servicio: ServicioTablas) -> None:
        self._servicio = servicio

    def ejecutar(
        self,
        documento: Documento,
        destino: Path,
        formato: FormatoTabla,
        progreso: Progreso | None = None,
    ) -> Path:
        escrito = self._servicio.exportar_texto_como_hoja(
            documento.id, destino, formato, progreso
        )
        if escrito is None:
            # Un PDF escaneado son imágenes: la hoja saldría en blanco.
            raise ErrorDominio(
                "El documento no tiene texto que volcar (¿es un PDF escaneado?): "
                "no se ha creado ningún fichero"
            )
        return escrito
