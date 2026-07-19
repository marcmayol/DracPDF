"""Fixtures de pytest para los tests de integración de adaptadores."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.adapters.generar_fixtures import generar_pdf_simple
from tests.adapters.generar_fixtures_formularios import (
    generar_formulario_completo,
    generar_xfa,
)


@pytest.fixture
def pdf_simple(tmp_path: Path) -> Path:
    """Ruta a un PDF de 3 páginas generado al vuelo en un directorio temporal."""
    return generar_pdf_simple(tmp_path / "simple.pdf")


@pytest.fixture
def pdf_formulario(tmp_path: Path) -> Path:
    """PDF con un campo de cada tipo (texto, casilla, radio, combo, lista)."""
    return generar_formulario_completo(tmp_path / "formulario.pdf")


@pytest.fixture
def pdf_xfa(tmp_path: Path) -> Path:
    """PDF con entrada /XFA en el AcroForm."""
    return generar_xfa(tmp_path / "xfa.pdf")
