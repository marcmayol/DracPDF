"""Localización de recursos (assets, iconos) en desarrollo y en el .exe.

En un ejecutable de PyInstaller los datos se extraen a `sys._MEIPASS`; en
desarrollo cuelgan de la raíz del repositorio.
"""

from __future__ import annotations

import sys
from pathlib import Path


def base_recursos() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # src/lectorpdf/recursos.py -> raíz del repo.
    return Path(__file__).resolve().parents[2]
