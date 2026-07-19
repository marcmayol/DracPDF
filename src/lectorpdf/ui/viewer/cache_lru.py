"""Caché LRU genérica. Vive en la UI (la caché de renders es asunto suyo)."""

from __future__ import annotations

from collections import OrderedDict


class CacheLRU[K, V]:
    """Caché de tamaño acotado que descarta el elemento menos usado recientemente."""

    def __init__(self, capacidad: int) -> None:
        if capacidad < 1:
            raise ValueError("La capacidad debe ser >= 1")
        self._capacidad = capacidad
        self._datos: OrderedDict[K, V] = OrderedDict()

    def obtener(self, clave: K) -> V | None:
        if clave not in self._datos:
            return None
        self._datos.move_to_end(clave)
        return self._datos[clave]

    def poner(self, clave: K, valor: V) -> None:
        self._datos[clave] = valor
        self._datos.move_to_end(clave)
        while len(self._datos) > self._capacidad:
            self._datos.popitem(last=False)

    def descartar(self, clave: K) -> None:
        """Elimina una entrada si existe (para invalidar renders concretos)."""
        self._datos.pop(clave, None)

    def limpiar(self) -> None:
        self._datos.clear()

    def claves(self) -> list[K]:
        return list(self._datos)

    def __contains__(self, clave: object) -> bool:
        return clave in self._datos

    def __len__(self) -> int:
        return len(self._datos)
