"""Verifica que el icono de ventana/barra de tareas usa el .ico multiresolución
con los tamaños 16/32 afinados del diseño (no un PNG de 256 reescalado)."""

from __future__ import annotations

import importlib.util
import struct
from pathlib import Path
from types import ModuleType

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from lectorpdf.ui.theme.marca import ruta_icono_app


def _mod() -> ModuleType:
    ruta = Path(__file__).resolve().parents[2] / "scripts" / "generar_iconos.py"
    spec = importlib.util.spec_from_file_location("generar_iconos", ruta)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _tamanos_del_ico(ico: bytes) -> set[int]:
    total = struct.unpack("<HHH", ico[:6])[2]
    tamanos = set()
    for i in range(total):
        ancho = ico[6 + 16 * i]  # primer byte de la entrada; 0 = 256
        tamanos.add(256 if ancho == 0 else ancho)
    return tamanos


def _pngs_afinados(mod: ModuleType) -> list[tuple[int, bytes]]:
    imagenes = []
    for tamano in (16, 32, 48, 256):
        png = mod._png_para(tamano)
        assert png is not None, f"falta el PNG afinado de {tamano}px"
        imagenes.append((tamano, png))
    return imagenes


def test_el_ico_contiene_los_tamanos_afinados() -> None:
    mod = _mod()
    imagenes = _pngs_afinados(mod)
    ico = mod._construir_ico(imagenes)

    assert {16, 32, 48, 256} <= _tamanos_del_ico(ico)
    # El 16 y el 256 son imágenes distintas (afinadas por tamaño, no reescaladas).
    por_tamano = dict(imagenes)
    assert por_tamano[16] != por_tamano[256]


def test_qicon_del_ico_expone_16_y_32(qapp: object, tmp_path: Path) -> None:
    mod = _mod()
    ico = mod._construir_ico(_pngs_afinados(mod))
    ruta = tmp_path / "ladon.ico"
    ruta.write_bytes(ico)

    tamanos = QIcon(str(ruta)).availableSizes()

    assert QSize(16, 16) in tamanos
    assert QSize(32, 32) in tamanos


def test_ruta_icono_app_prefiere_el_ico() -> None:
    mod = _mod()
    assert mod.main() == 0  # genera build/icons/ladon.ico desde los PNG afinados

    ruta = ruta_icono_app()
    assert ruta is not None and ruta.suffix == ".ico"
