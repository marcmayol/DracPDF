"""Suavizado de trazos por interpolación con curvas (Catmull-Rom -> Bézier).

Puro y sin Qt para poder testearlo aislado. Convierte los puntos capturados en
segmentos de Bézier cúbica que pasan por ellos, evitando la polilínea cruda.
"""

from __future__ import annotations

Punto = tuple[float, float]
# Segmento de Bézier cúbica: (inicio, control1, control2, fin).
Segmento = tuple[Punto, Punto, Punto, Punto]


def curva_catmull_rom(puntos: list[Punto]) -> list[Segmento]:
    """Devuelve los segmentos de Bézier de una spline Catmull-Rom uniforme.

    Para cada par de puntos consecutivos (p1, p2), con vecinos p0 y p3:
        c1 = p1 + (p2 - p0) / 6
        c2 = p2 - (p3 - p1) / 6
    En los extremos el vecino que falta se duplica con el propio punto.
    """
    n = len(puntos)
    if n < 2:
        return []

    segmentos: list[Segmento] = []
    for i in range(n - 1):
        p0 = puntos[i - 1] if i > 0 else puntos[i]
        p1 = puntos[i]
        p2 = puntos[i + 1]
        p3 = puntos[i + 2] if i + 2 < n else puntos[i + 1]

        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        segmentos.append((p1, c1, c2, p2))
    return segmentos
