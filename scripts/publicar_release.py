"""Publica una release de DracPDF y actualiza el manifiesto de actualizaciones.

Ritual completo: build del exe, compilación del instalador (con la versión
inyectada al .iss), cálculo del sha256, creación de la Release en GitHub con el
asset (gh CLI, sin secretos en el repo) y actualización + publicación del
manifiesto docs/updates.json (GitHub Pages).

La versión sale de la fuente única: src/lectorpdf/__init__.py (__version__).

Cinturón de seguridad: tras construir, se verifica que el instalador generado
lleva exactamente __version__ en su nombre y que el sha256 que se va a escribir en
el manifiesto es el del fichero construido; si algo no cuadra, aborta sin publicar.

Uso:
    uv run python scripts/publicar_release.py             # construye y publica
    uv run python scripts/publicar_release.py --dry-run    # prepara sin publicar
    uv run python scripts/publicar_release.py --notas "…"  # notas de la versión
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MANIFIESTO = RAIZ / "docs" / "updates.json"

sys.path.insert(0, str(RAIZ / "src"))
from lectorpdf import __version__  # noqa: E402  (fuente única de la versión)

_REPO = "marcmayol/DracPDF"
_CHECK_HORAS = 24


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def url_release(version: str) -> str:
    return (
        f"https://github.com/{_REPO}/releases/download/"
        f"v{version}/DracPDF-{version}-setup.exe"
    )


def generar_manifiesto(version: str, sha: str, notas: str) -> dict[str, object]:
    return {
        "version": version,
        "url": url_release(version),
        "sha256": sha,
        "notas": notas or f"DracPDF {version}.",
        "check_horas": _CHECK_HORAS,
        "canal": None,
        "porcentaje_despliegue": None,
    }


def verificar_coherencia(
    version: str, instalador: Path, manifiesto: dict[str, object]
) -> None:
    """Cinturón: nombre del instalador, versión y sha del manifiesto coherentes."""
    esperado = f"DracPDF-{version}-setup.exe"
    if instalador.name != esperado:
        raise SystemExit(
            f"El instalador construido es {instalador.name!r}, se esperaba "
            f"{esperado!r}: la versión del build no coincide con __version__."
        )
    if manifiesto["version"] != version:
        raise SystemExit("La versión del manifiesto no coincide con __version__.")
    real = sha256(instalador)
    if manifiesto["sha256"] != real:
        raise SystemExit(
            "El sha256 del manifiesto no coincide con el instalador construido."
        )


def construir_todo() -> Path:
    """Construye exe + instalador y devuelve la ruta del instalador."""
    _ejecutar([sys.executable, str(RAIZ / "scripts" / "construir_exe.py")])
    _ejecutar([sys.executable, str(RAIZ / "scripts" / "construir_instalador.py")])
    instalador = RAIZ / "dist" / "installer" / f"DracPDF-{__version__}-setup.exe"
    if not instalador.is_file():
        raise SystemExit(f"No se generó el instalador esperado: {instalador}")
    return instalador


def preparar(
    notas: str,
    construir: Callable[[], Path] = construir_todo,
    destino_manifiesto: Path = MANIFIESTO,
) -> tuple[dict[str, object], Path]:
    """Construye, genera y escribe el manifiesto tras verificar la coherencia.
    Devuelve ``(manifiesto, instalador)``. No publica nada (eso es `publicar`)."""
    version = __version__
    instalador = construir()
    manifiesto = generar_manifiesto(version, sha256(instalador), notas)
    verificar_coherencia(version, instalador, manifiesto)
    destino_manifiesto.parent.mkdir(parents=True, exist_ok=True)
    destino_manifiesto.write_text(
        json.dumps(manifiesto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifiesto, instalador


def publicar(instalador: Path, notas: str) -> None:
    """Crea la Release en GitHub con el asset y publica el manifiesto (Pages)."""
    version = __version__
    _ejecutar(
        [
            "gh",
            "release",
            "create",
            f"v{version}",
            str(instalador),
            "--title",
            f"DracPDF {version}",
            "--notes",
            notas or f"DracPDF {version}.",
        ]
    )
    _ejecutar(["git", "add", str(MANIFIESTO)])
    _ejecutar(["git", "commit", "-m", f"Publica el manifiesto de la {version}"])
    _ejecutar(["git", "push", "origin", "main"])


def _ejecutar(cmd: list[str]) -> None:
    print("»", " ".join(cmd))
    if subprocess.call(cmd, cwd=str(RAIZ)) != 0:
        raise SystemExit(f"Falló: {' '.join(cmd)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publica una release de DracPDF.")
    parser.add_argument("--dry-run", action="store_true", help="prepara sin publicar")
    parser.add_argument("--notas", default="", help="notas de la versión")
    args = parser.parse_args(argv)

    manifiesto, instalador = preparar(args.notas)
    sha_corto = str(manifiesto["sha256"])[:12]
    print(f"Manifiesto {manifiesto['version']} (sha256 {sha_corto}…)")
    print(f"Instalador: {instalador}")
    if args.dry_run:
        print("--dry-run: preparado sin publicar (Release y manifiesto no subidos).")
        return 0
    publicar(instalador, args.notas)
    print(f"Release v{__version__} publicada y manifiesto actualizado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
