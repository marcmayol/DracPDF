"""Compila el instalador de Windows de DracPDF con Inno Setup.

Requiere el .exe (scripts/construir_exe.py) y el compilador ISCC de Inno Setup.
El resultado queda en dist/installer/DracPDF-<versión>-setup.exe (no versionado).

Uso:
    uv run python scripts/construir_instalador.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ISS = RAIZ / "scripts" / "dracpdf.iss"

sys.path.insert(0, str(RAIZ / "src"))
from lectorpdf import __version__  # noqa: E402  (fuente única de la versión)

_CANDIDATOS_ISCC = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
    Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
]


def _buscar_iscc() -> str:
    en_path = shutil.which("ISCC")
    if en_path:
        return en_path
    for candidato in _CANDIDATOS_ISCC:
        if candidato.is_file():
            return str(candidato)
    raise SystemExit(
        "No se encontró ISCC.exe. Instala Inno Setup 6 "
        "(winget install JRSoftware.InnoSetup) y reintenta."
    )


def main() -> int:
    if not (RAIZ / "dist" / "DracPDF.exe").is_file():
        raise SystemExit(
            "Falta dist/DracPDF.exe. Ejecuta antes: uv run python scripts/construir_exe.py"
        )
    iscc = _buscar_iscc()
    print(f"Compilando instalador {__version__} con:", iscc)
    return subprocess.call(
        [iscc, f"/DMyAppVersion={__version__}", str(ISS)], cwd=str(RAIZ)
    )


if __name__ == "__main__":
    raise SystemExit(main())
