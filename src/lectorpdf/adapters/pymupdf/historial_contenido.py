"""Historial de operaciones de contenido (Fase 9): texto, corrección, imágenes.

Patrón comando: cada operación guarda cómo deshacerse (restaurar el content
stream de la página, descartando lo añadido) y cómo rehacerse (re-ejecutar la
operación). Es paralelo al historial de valores de formularios (Fase 8): la misma
acción Ctrl+Z/menú los cubre a ambos. Vive junto al documento en el registro y se
descarta al cerrar o reabrir.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class OperacionContenido:
    #: Páginas cuyo render debe invalidarse al aplicar/revertir la operación.
    paginas: tuple[int, ...]
    deshacer: Callable[[], None]
    rehacer: Callable[[], None]


class HistorialContenido:
    def __init__(self) -> None:
        self._pila_deshacer: list[OperacionContenido] = []
        self._pila_rehacer: list[OperacionContenido] = []

    def registrar(self, operacion: OperacionContenido) -> None:
        """Apila una operación ya ejecutada; invalida el rehacer pendiente."""
        self._pila_deshacer.append(operacion)
        self._pila_rehacer.clear()

    def puede_deshacer(self) -> bool:
        return bool(self._pila_deshacer)

    def puede_rehacer(self) -> bool:
        return bool(self._pila_rehacer)

    def deshacer(self) -> OperacionContenido | None:
        if not self._pila_deshacer:
            return None
        operacion = self._pila_deshacer.pop()
        operacion.deshacer()
        self._pila_rehacer.append(operacion)
        return operacion

    def rehacer(self) -> OperacionContenido | None:
        if not self._pila_rehacer:
            return None
        operacion = self._pila_rehacer.pop()
        operacion.rehacer()
        self._pila_deshacer.append(operacion)
        return operacion
