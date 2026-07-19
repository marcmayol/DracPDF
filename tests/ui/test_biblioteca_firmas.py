"""Tests de la biblioteca de firmas (contra ficheros reales, sin Qt)."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.ui.signature.biblioteca_firmas import (
    BibliotecaFirmas,
    FirmaNoEncontrada,
)

_PNG = b"\x89PNG\r\n\x1a\n-firma"


def test_guardar_crea_png_y_sidecar_json(tmp_path: Path) -> None:
    biblioteca = BibliotecaFirmas(tmp_path / "firmas")

    firma = biblioteca.guardar("Mi firma", _PNG)

    assert firma.ruta_png.exists()
    assert (firma.ruta_png.parent / f"{firma.id}.json").exists()
    assert firma.nombre == "Mi firma"


def test_guardar_escribe_png_antes_que_json(tmp_path: Path) -> None:
    biblioteca = BibliotecaFirmas(tmp_path / "firmas")

    firma = biblioteca.guardar("F", _PNG)

    png = firma.ruta_png
    sidecar = png.parent / f"{firma.id}.json"
    # El PNG no puede ser más nuevo que el JSON (se escribió antes).
    assert png.stat().st_mtime_ns <= sidecar.stat().st_mtime_ns


def test_listar_devuelve_las_firmas_guardadas(tmp_path: Path) -> None:
    biblioteca = BibliotecaFirmas(tmp_path / "firmas")
    biblioteca.guardar("A", _PNG)
    biblioteca.guardar("B", _PNG)

    nombres = {f.nombre for f in biblioteca.listar()}

    assert nombres == {"A", "B"}


def test_listar_ignora_png_huerfano_sin_sidecar(tmp_path: Path) -> None:
    directorio = tmp_path / "firmas"
    biblioteca = BibliotecaFirmas(directorio)
    biblioteca.guardar("A", _PNG)
    # Simula un alta a medias: PNG sin su JSON.
    (directorio / "huerfano.png").write_bytes(_PNG)

    firmas = biblioteca.listar()

    assert len(firmas) == 1
    assert firmas[0].nombre == "A"


def test_listar_directorio_inexistente_es_vacio(tmp_path: Path) -> None:
    biblioteca = BibliotecaFirmas(tmp_path / "no_existe")

    assert biblioteca.listar() == []


def test_cargar_devuelve_los_bytes_del_png(tmp_path: Path) -> None:
    biblioteca = BibliotecaFirmas(tmp_path / "firmas")
    firma = biblioteca.guardar("A", _PNG)

    assert biblioteca.cargar(firma.id) == _PNG


def test_cargar_id_inexistente_lanza(tmp_path: Path) -> None:
    biblioteca = BibliotecaFirmas(tmp_path / "firmas")

    with pytest.raises(FirmaNoEncontrada):
        biblioteca.cargar("desconocido")


def test_eliminar_borra_png_y_sidecar(tmp_path: Path) -> None:
    biblioteca = BibliotecaFirmas(tmp_path / "firmas")
    firma = biblioteca.guardar("A", _PNG)

    biblioteca.eliminar(firma.id)

    assert biblioteca.listar() == []
    with pytest.raises(FirmaNoEncontrada):
        biblioteca.cargar(firma.id)
