"""Tests de scripts/publicar_release.py: preparación del manifiesto y cinturón
de coherencia de versión, sin construir de verdad ni publicar."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


def _cargar() -> ModuleType:
    ruta = Path(__file__).resolve().parents[1] / "scripts" / "publicar_release.py"
    spec = importlib.util.spec_from_file_location("publicar_release", ruta)
    assert spec is not None and spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _instalador_falso(directorio: Path, version: str, contenido: bytes) -> Path:
    ruta = directorio / f"DracPDF-{version}-setup.exe"
    ruta.write_bytes(contenido)
    return ruta


def test_preparar_genera_manifiesto_con_sha_coincidente(tmp_path: Path) -> None:
    mod = _cargar()
    version = mod.__version__
    contenido = b"instalador-de-prueba-1234"
    instalador = _instalador_falso(tmp_path, version, contenido)
    destino = tmp_path / "updates.json"

    manifiesto, devuelto = mod.preparar(
        "Notas de prueba",
        construir=lambda: instalador,
        destino_manifiesto=destino,
    )

    assert devuelto == instalador
    assert manifiesto["version"] == version
    assert manifiesto["sha256"] == hashlib.sha256(contenido).hexdigest()
    assert f"v{version}" in str(manifiesto["url"])
    # El manifiesto escrito en disco es JSON válido y coincide.
    escrito = json.loads(destino.read_text(encoding="utf-8"))
    assert escrito["sha256"] == manifiesto["sha256"]
    assert escrito["version"] == version


def test_verificar_coherencia_aborta_si_nombre_no_coincide(tmp_path: Path) -> None:
    mod = _cargar()
    malo = tmp_path / "DracPDF-9.9.9-setup.exe"
    malo.write_bytes(b"x")
    manifiesto = mod.generar_manifiesto(mod.__version__, mod.sha256(malo), "n")
    with pytest.raises(SystemExit):
        mod.verificar_coherencia(mod.__version__, malo, manifiesto)


def test_verificar_coherencia_aborta_si_sha_no_coincide(tmp_path: Path) -> None:
    mod = _cargar()
    version = mod.__version__
    instalador = _instalador_falso(tmp_path, version, b"contenido")
    manifiesto = mod.generar_manifiesto(version, "00" * 32, "n")  # sha falso
    with pytest.raises(SystemExit):
        mod.verificar_coherencia(version, instalador, manifiesto)


def test_main_dry_run_no_publica(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _cargar()
    version = mod.__version__
    instalador = _instalador_falso(tmp_path, version, b"abc")
    publicado: list[bool] = []
    monkeypatch.setattr(
        mod,
        "preparar",
        lambda notas: (
            mod.generar_manifiesto(version, mod.sha256(instalador), notas),
            instalador,
        ),
    )
    monkeypatch.setattr(mod, "publicar", lambda *a, **k: publicado.append(True))

    assert mod.main(["--dry-run"]) == 0
    assert publicado == []  # dry-run no publica


def test_main_sin_dry_run_publica(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _cargar()
    version = mod.__version__
    instalador = _instalador_falso(tmp_path, version, b"abc")
    publicado: list[bool] = []
    monkeypatch.setattr(
        mod,
        "preparar",
        lambda notas: (
            mod.generar_manifiesto(version, mod.sha256(instalador), notas),
            instalador,
        ),
    )
    monkeypatch.setattr(mod, "publicar", lambda *a, **k: publicado.append(True))

    assert mod.main([]) == 0
    assert publicado == [True]
