"""Entidades de dominio para las herramientas de PDF (Fase 6)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

#: Callback de progreso del dominio: (hecho, total). La UI lo conecta a sus
#: señales; para cancelar, la implementación puede lanzar OperacionCancelada.
Progreso = Callable[[int, int], None]


@dataclass(frozen=True)
class Rango:
    """Rango de páginas 1-based, inclusivo por ambos extremos."""

    inicio: int
    fin: int

    def __post_init__(self) -> None:
        if self.inicio < 1 or self.fin < self.inicio:
            raise ValueError(f"Rango inválido: {self.inicio}-{self.fin}")


@dataclass(frozen=True)
class ResultadoCompresion:
    bytes_antes: int
    bytes_despues: int

    @property
    def porcentaje_reduccion(self) -> float:
        if self.bytes_antes <= 0:
            return 0.0
        return 100.0 * (self.bytes_antes - self.bytes_despues) / self.bytes_antes
