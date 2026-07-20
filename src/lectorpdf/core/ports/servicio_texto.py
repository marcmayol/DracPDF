"""Puerto de extracción de palabras de una página (para seleccionar y copiar).

Solo lectura del documento abierto. Devuelve las palabras en orden de lectura,
con su rectángulo en puntos PDF, para poder mapearlas a la escena con la misma
traducción que los formularios.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.contenido import PalabraTexto


@runtime_checkable
class ServicioTexto(Protocol):
    def palabras(self, documento_id: str, pagina: int) -> tuple[PalabraTexto, ...]: ...
