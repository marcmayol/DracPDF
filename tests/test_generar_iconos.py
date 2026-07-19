"""Tests del ensamblado del .ico (sin necesitar los PNG de marca reales)."""

from __future__ import annotations

import importlib.util
import struct
from pathlib import Path
from types import ModuleType


def _cargar_script() -> ModuleType:
    ruta = Path(__file__).resolve().parents[1] / "scripts" / "generar_iconos.py"
    spec = importlib.util.spec_from_file_location("generar_iconos", ruta)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_construir_ico_cabecera_entradas_y_datos() -> None:
    mod = _cargar_script()
    png_16 = b"\x89PNG\r\n\x1a\n" + b"a" * 20
    png_256 = b"\x89PNG\r\n\x1a\n" + b"b" * 40

    ico = mod._construir_ico([(16, png_16), (256, png_256)])

    reservado, tipo, total = struct.unpack("<HHH", ico[:6])
    assert (reservado, tipo, total) == (0, 1, 2)

    # Entrada 1: 16x16, 32 bits, tamaño del primer PNG.
    ancho, alto, _, _, planos, bits, tam, offset = struct.unpack(
        "<BBBBHHII", ico[6:22]
    )
    assert (ancho, alto, planos, bits) == (16, 16, 1, 32)
    assert tam == len(png_16)
    assert offset == 6 + 16 * 2

    # Entrada 2: 256 se codifica como ancho/alto 0.
    ancho2 = struct.unpack("<BBBBHHII", ico[22:38])[0]
    assert ancho2 == 0

    # Los PNG van embebidos al final.
    assert png_16 in ico and png_256 in ico


def test_main_avisa_si_faltan_los_png_fuente(capsys) -> None:  # type: ignore[no-untyped-def]
    mod = _cargar_script()
    # Si los PNG de marca no están, el script sale con código 1 y explica qué falta.
    codigo = mod.main()
    salida = capsys.readouterr().out
    if codigo == 1:
        assert "FALTAN" in salida
    else:
        assert "Iconos generados" in salida
