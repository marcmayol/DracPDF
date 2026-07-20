"""Historial de ediciones de formulario por documento (deshacer/rehacer).

Estructura pura (sin fitz), propiedad del registro: se crea con el documento y se
descarta al cerrarlo, con la misma disciplina que las marcas. Guarda una pila de
ediciones con una posición; registrar una nueva descarta el 'rehacer' pendiente.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Edicion:
    campo_id: str
    antes: str
    despues: str


class HistorialEdiciones:
    def __init__(self) -> None:
        self._ediciones: list[Edicion] = []
        self._pos = 0  # número de ediciones actualmente aplicadas

    def registrar(self, campo_id: str, antes: str, despues: str) -> None:
        del self._ediciones[self._pos :]  # una edición nueva invalida el rehacer
        self._ediciones.append(Edicion(campo_id, antes, despues))
        self._pos += 1

    def puede_deshacer(self) -> bool:
        return self._pos > 0

    def puede_rehacer(self) -> bool:
        return self._pos < len(self._ediciones)

    def deshacer(self) -> Edicion | None:
        if not self.puede_deshacer():
            return None
        self._pos -= 1
        return self._ediciones[self._pos]

    def rehacer(self) -> Edicion | None:
        if not self.puede_rehacer():
            return None
        edicion = self._ediciones[self._pos]
        self._pos += 1
        return edicion
