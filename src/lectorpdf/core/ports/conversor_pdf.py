"""Puerto de conversiones salientes del documento abierto (PDF → otros formatos).

Operan sobre el documento abierto (por `documento_id`) y escriben a un fichero de
destino. Recorren páginas, así que aceptan el callback de progreso del dominio
(para el worker de la UI). Las conversiones LEEN el documento: se permiten aunque
esté firmado.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.herramientas import Progreso, Rango


@runtime_checkable
class ConversorPDF(Protocol):
    def a_word(
        self,
        documento_id: str,
        destino: Path,
        rango: Rango | None = None,
        progreso: Progreso | None = None,
    ) -> None: ...

    def a_html(
        self,
        documento_id: str,
        destino: Path,
        rango: Rango | None = None,
        imagenes_embebidas: bool = True,
        progreso: Progreso | None = None,
    ) -> None: ...

    def a_markdown(
        self,
        documento_id: str,
        destino: Path,
        rango: Rango | None = None,
        progreso: Progreso | None = None,
    ) -> None: ...

    def es_escaneado(self, documento_id: str) -> bool:
        """True si el PDF no tiene capa de texto (la conversión saldría vacía)."""
        ...
