"""Localización de los assets de marca (logo e icono de la app).

Las rutas se resuelven desde la raíz del repo. Devuelven None si el asset aún no
está (los binarios de marca son fuente que se descarga del diseño; el .ico es
derivado y lo genera scripts/generar_iconos.py), para que la UI degrade con
elegancia en vez de fallar.
"""

from __future__ import annotations

from pathlib import Path

NOMBRE_APP = "DracPDF"

_RAIZ = Path(__file__).resolve().parents[4]
_DIR_BRAND = _RAIZ / "assets" / "brand"
_DIR_ICONOS_BUILD = _RAIZ / "build" / "icons"
_SVG_INTERINO = _DIR_BRAND / "dragon.svg"


def ruta_icono_app() -> Path | None:
    """.ico multiresolución si ya se generó; si no, el PNG de 256 o el SVG interino."""
    for candidata in (
        _DIR_ICONOS_BUILD / "ladon.ico",
        _DIR_BRAND / "png" / "icon-256.png",
        _SVG_INTERINO,
    ):
        if candidata.is_file():
            return candidata
    return None


def ruta_logo(es_oscuro: bool) -> Path | None:
    """Logo para el "acerca de": silueta del dragón (negativo blanco sobre tema
    oscuro, tinta en claro) o, si aún no está, el SVG de marca interino."""
    nombre = "dragon-silhouette-white.png" if es_oscuro else "dragon-silhouette.png"
    raster = _DIR_BRAND / nombre
    if raster.is_file():
        return raster
    return _SVG_INTERINO if _SVG_INTERINO.is_file() else None
