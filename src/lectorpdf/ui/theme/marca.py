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


def ruta_icono_app() -> Path | None:
    """.ico multiresolución si ya se generó; si no, el PNG de 256 fuente."""
    ico = _DIR_ICONOS_BUILD / "ladon.ico"
    if ico.is_file():
        return ico
    png = _DIR_BRAND / "png" / "icon-256.png"
    return png if png.is_file() else None


def ruta_logo(es_oscuro: bool) -> Path | None:
    """Silueta del dragón: negativo (blanca) sobre tema oscuro, tinta en claro."""
    nombre = "dragon-silhouette-white.png" if es_oscuro else "dragon-silhouette.png"
    ruta = _DIR_BRAND / nombre
    return ruta if ruta.is_file() else None
