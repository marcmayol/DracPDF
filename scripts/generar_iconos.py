"""Genera los iconos de la aplicación a partir de los PNG de marca.

Fuente (versionada): los PNG afinados a mano por tamaño del diseño "Ladón" en
`assets/brand/png/icon-{16,32,48,256}.png`.
Salida (derivada, NO versionada, en `build/icons/`):
  - `ladon.ico`  : icono multiresolución de Windows (16/32/48/256), PNG-in-ICO.
  - `ladon-{n}.png` : copias por tamaño para Linux (hicolor).

Uso:
    uv run python scripts/generar_iconos.py
"""

from __future__ import annotations

import shutil
import struct
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "assets" / "brand" / "png"
DESTINO = RAIZ / "build" / "icons"
TAMANOS = (16, 32, 48, 256)


def _construir_ico(imagenes: list[tuple[int, bytes]]) -> bytes:
    """Ensambla un .ico con cada PNG embebido (soportado por Windows Vista+)."""
    total = len(imagenes)
    cabecera = struct.pack("<HHH", 0, 1, total)  # reservado, tipo=1 (icono), nº
    entradas = b""
    datos = b""
    offset = 6 + 16 * total
    for tamano, png in imagenes:
        ancho = 0 if tamano >= 256 else tamano  # 0 = 256 en el formato ICO
        alto = ancho
        entradas += struct.pack(
            "<BBBBHHII", ancho, alto, 0, 0, 1, 32, len(png), offset
        )
        datos += png
        offset += len(png)
    return cabecera + entradas + datos


def main() -> int:
    faltan = [t for t in TAMANOS if not (ORIGEN / f"icon-{t}.png").is_file()]
    if faltan:
        print("FALTAN los PNG de marca fuente en:", ORIGEN)
        for t in faltan:
            print(f"  - icon-{t}.png")
        print(
            "Descárgalos del proyecto de Claude Design (assets/brand/png/) y vuelve a "
            "ejecutar. Son la fuente versionada del icono."
        )
        return 1

    DESTINO.mkdir(parents=True, exist_ok=True)
    imagenes: list[tuple[int, bytes]] = []
    generados: list[Path] = []
    for tamano in TAMANOS:
        png = (ORIGEN / f"icon-{tamano}.png").read_bytes()
        imagenes.append((tamano, png))
        salida_png = DESTINO / f"ladon-{tamano}.png"
        shutil.copyfile(ORIGEN / f"icon-{tamano}.png", salida_png)
        generados.append(salida_png)

    ico = DESTINO / "ladon.ico"
    ico.write_bytes(_construir_ico(imagenes))
    generados.insert(0, ico)

    print(f"Iconos generados en {DESTINO}:")
    for ruta in generados:
        print(f"  - {ruta.name} ({ruta.stat().st_size} bytes)")
    print(f"ICO multiresolución con tamaños: {', '.join(map(str, TAMANOS))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
