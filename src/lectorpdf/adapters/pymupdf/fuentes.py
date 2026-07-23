"""Fuentes OFL embebibles para el texto nuevo (Fase 9).

Se empaquetan en `assets/fonts/` y se registran en la página con `insert_font`
antes de escribir, de modo que el PDF resultante embebe la fuente (Type0) y se ve
igual en cualquier máquina. Nada de fuentes del sistema.
"""

from __future__ import annotations

from lectorpdf.core.domain.anotaciones import FuenteTexto
from lectorpdf.recursos import base_recursos

_ARCHIVOS = {
    FuenteTexto.SERIF: "SourceSerif4-Regular.ttf",
    FuenteTexto.SANS: "SourceSans3-Regular.ttf",
    FuenteTexto.MONO: "JetBrainsMono-Regular.ttf",
}

# Nombre interno estable con el que se registra la fuente en cada página.
_NOMBRE = {
    FuenteTexto.SERIF: "ff-serif",
    FuenteTexto.SANS: "ff-sans",
    FuenteTexto.MONO: "ff-mono",
}


def ruta_fuente(fuente: FuenteTexto) -> str:
    return str(base_recursos() / "assets" / "fonts" / _ARCHIVOS[fuente])


def nombre_fuente(fuente: FuenteTexto) -> str:
    return _NOMBRE[fuente]
