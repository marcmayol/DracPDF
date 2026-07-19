"""Genera los iconos de la aplicación a partir de la marca.

Fuente (versionada), por orden de preferencia:
  1. PNG afinados a mano por tamaño en `assets/brand/png/icon-{16,32,48,256}.png`
     (los del diseño "Ladón"; mejores a tamaño pequeño).
  2. Si faltan, el SVG de marca `assets/brand/dragon.svg` (marca interina
     vectorial), que se rasteriza a cada tamaño.

Salida (derivada, NO versionada, en `build/icons/`):
  - `ladon.ico`     : icono multiresolución de Windows (16/32/48/256), PNG-in-ICO.
  - `ladon-{n}.png` : copias por tamaño para Linux (hicolor).

Uso:
    uv run python scripts/generar_iconos.py
"""

from __future__ import annotations

import os
import struct
from pathlib import Path

# Rasterizar el SVG sin pantalla real.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN_PNG = RAIZ / "assets" / "brand" / "png"
ORIGEN_SVG = RAIZ / "assets" / "brand" / "dragon.svg"
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


def _png_desde_svg(tamano: int) -> bytes:
    from PySide6.QtCore import QBuffer, QByteArray, QIODeviceBase, Qt
    from PySide6.QtGui import QImage, QImageWriter, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    renderizador = QSvgRenderer(str(ORIGEN_SVG))
    imagen = QImage(tamano, tamano, QImage.Format.Format_ARGB32)
    imagen.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(imagen)
    renderizador.render(pintor)
    pintor.end()

    datos = QByteArray()
    buffer = QBuffer(datos)
    buffer.open(QIODeviceBase.OpenModeFlag.WriteOnly)
    QImageWriter(buffer, QByteArray(b"PNG")).write(imagen)
    return bytes(datos.data())


def _png_para(tamano: int) -> bytes | None:
    afinado = ORIGEN_PNG / f"icon-{tamano}.png"
    if afinado.is_file():
        return afinado.read_bytes()
    if ORIGEN_SVG.is_file():
        return _png_desde_svg(tamano)
    return None


def main() -> int:
    imagenes: list[tuple[int, bytes]] = []
    faltan = []
    for tamano in TAMANOS:
        png = _png_para(tamano)
        if png is None:
            faltan.append(tamano)
        else:
            imagenes.append((tamano, png))

    if faltan:
        print("No hay fuente de marca para los tamaños:", faltan)
        print(
            "Coloca los PNG en assets/brand/png/ o el SVG en "
            "assets/brand/dragon.svg y vuelve a ejecutar."
        )
        return 1

    usa_afinados = (ORIGEN_PNG / "icon-256.png").is_file()
    DESTINO.mkdir(parents=True, exist_ok=True)
    generados: list[Path] = []
    for tamano, png in imagenes:
        salida = DESTINO / f"ladon-{tamano}.png"
        salida.write_bytes(png)
        generados.append(salida)

    ico = DESTINO / "ladon.ico"
    ico.write_bytes(_construir_ico(imagenes))
    generados.insert(0, ico)

    fuente = "PNG afinados del diseño" if usa_afinados else "SVG de marca interino"
    print(f"Fuente: {fuente}")
    print(f"Iconos generados en {DESTINO}:")
    for ruta in generados:
        print(f"  - {ruta.name} ({ruta.stat().st_size} bytes)")
    print(f"ICO multiresolución con tamaños: {', '.join(map(str, TAMANOS))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
