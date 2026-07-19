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


def main() -> int:
    sys.path.insert(0, str(RAIZ / "scripts"))
    _generar_icono()

    ico = RAIZ / "build" / "icons" / "ladon.ico"
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
