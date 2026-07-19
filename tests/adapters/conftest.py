"""Fixtures de pytest para los tests de integración de adaptadores."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.adapters.generar_fixtures import generar_pdf_simple


@pytest.fixture
def pdf_simple(tmp_path: Path) -> Path:
    """Ruta a un PDF de 3 páginas generado al vuelo en un directorio temporal."""
    return generar_pdf_simple(tmp_path / "simple.pdf")
