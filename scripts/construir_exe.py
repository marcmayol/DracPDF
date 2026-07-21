"""Construye el ejecutable de Windows DracPDF.exe con PyInstaller.

Genera primero el icono (.ico) y luego empaqueta la app en un único .exe con los
assets (iconos SVG, marca) incluidos.

Uso:
    uv run python scripts/construir_exe.py
El resultado queda en dist/DracPDF.exe (no versionado).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _generar_icono() -> None:
    import generar_iconos  # noqa: PLC0415  (mismo directorio scripts/)

    if generar_iconos.main() != 0:
        raise SystemExit("No se pudo generar el icono (falta la marca).")


def _dir_traducciones() -> Path:
    """Directorio de traducciones .qm de PySide6 (qtbase_es, qt_es…)."""
    import PySide6  # noqa: PLC0415

    return Path(PySide6.__file__).resolve().parent / "translations"


def main() -> int:
    sys.path.insert(0, str(RAIZ / "scripts"))
    _generar_icono()

    ico = RAIZ / "build" / "icons" / "ladon.ico"
    trad = _dir_traducciones()
    sep = ";" if sys.platform == "win32" else ":"
    orden = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--name",
        "DracPDF",
        "--onefile",
        "--windowed",
        "--icon",
        str(ico),
        "--paths",
        str(RAIZ / "src"),
        "--add-data",
        f"{RAIZ / 'assets'}{sep}assets",
        "--add-data",
        f"{ico.parent}{sep}build/icons",
        # Traducciones estándar de Qt en español (OK/Cancel/Close…).
        "--add-data",
        f"{trad / 'qtbase_es.qm'}{sep}PySide6/translations",
        "--add-data",
        f"{trad / 'qt_es.qm'}{sep}PySide6/translations",
        "--collect-submodules",
        "pyhanko",
        "--collect-submodules",
        "pyhanko_certvalidator",
        str(RAIZ / "scripts" / "dracpdf_launcher.py"),
    ]
    print("Ejecutando:", " ".join(orden))
    return subprocess.call(orden, cwd=str(RAIZ))


if __name__ == "__main__":
    raise SystemExit(main())
