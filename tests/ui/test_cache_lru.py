"""Tests de la caché LRU (sin dependencias de Qt)."""

from __future__ import annotations

import pytest

from lectorpdf.ui.viewer.cache_lru import CacheLRU


def test_guarda_y_recupera() -> None:
    cache: CacheLRU[str, int] = CacheLRU(capacidad=2)
    cache.poner("a", 1)

    assert cache.obtener("a") == 1
    assert cache.obtener("inexistente") is None


def test_descarta_el_menos_usado_recientemente() -> None:
    cache: CacheLRU[str, int] = CacheLRU(capacidad=2)
    cache.poner("a", 1)
    cache.poner("b", 2)
    cache.obtener("a")  # "a" pasa a ser el más reciente
    cache.poner("c", 3)  # desaloja "b"

    assert "a" in cache
    assert "c" in cache
    assert "b" not in cache
    assert len(cache) == 2


def test_poner_clave_existente_actualiza_valor_sin_crecer() -> None:
    cache: CacheLRU[str, int] = CacheLRU(capacidad=2)
    cache.poner("a", 1)
    cache.poner("a", 10)

    assert cache.obtener("a") == 10
    assert len(cache) == 1


def test_capacidad_invalida() -> None:
    with pytest.raises(ValueError):
        CacheLRU(capacidad=0)
