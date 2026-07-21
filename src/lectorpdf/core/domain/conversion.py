"""Entidades de dominio para las conversiones de formato (Fase 7).

Sin dependencias de infraestructura. El rango de páginas se reutiliza de
`herramientas.Rango` (1-based, inclusivo). `ConfigPagina` describe el tamaño y
los márgenes del PDF generado desde Word.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigPagina:
    """Tamaño de página y margen (en milímetros) para Word→PDF."""

    ancho_mm: float = 210.0  # A4 por defecto
    alto_mm: float = 297.0
    margen_mm: float = 20.0

    def __post_init__(self) -> None:
        if self.ancho_mm <= 0 or self.alto_mm <= 0 or self.margen_mm < 0:
            raise ValueError("Dimensiones o margen inválidos")


A4 = ConfigPagina()
CARTA = ConfigPagina(ancho_mm=215.9, alto_mm=279.4)
