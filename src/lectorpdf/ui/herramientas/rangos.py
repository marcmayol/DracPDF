"""Parseo del texto de rangos de páginas de la UI (p. ej. "1-3, 4-8, 10")."""

from __future__ import annotations

from lectorpdf.core.domain.herramientas import Rango


def parsear_rango(texto: str) -> Rango | None:
    """Convierte un rango único ("1-3", "5") en Rango, o None si está vacío
    (documento completo). Lanza ValueError si el texto está mal formado."""
    texto = texto.strip()
    if not texto:
        return None
    if "-" in texto:
        inicio_txt, fin_txt = texto.split("-", 1)
        return Rango(int(inicio_txt), int(fin_txt))
    n = int(texto)
    return Rango(n, n)


def parsear_rangos(texto: str) -> list[Rango]:
    """Convierte "1-3, 4-8, 10" en una lista de Rango. Lanza ValueError si el
    texto está mal formado."""
    rangos: list[Rango] = []
    for parte in texto.replace(";", ",").split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte:
            inicio_txt, fin_txt = parte.split("-", 1)
            rangos.append(Rango(int(inicio_txt), int(fin_txt)))
        else:
            n = int(parte)
            rangos.append(Rango(n, n))
    if not rangos:
        raise ValueError("No se indicó ningún rango")
    return rangos
