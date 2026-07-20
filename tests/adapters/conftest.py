"""Fixtures de pytest para los tests de integración de adaptadores."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.adapters.certificado_prueba import generar_pkcs12
from tests.adapters.generar_fixtures import generar_pdf_contenido, generar_pdf_simple
from tests.adapters.generar_fixtures_formularios import (
    generar_formulario_completo,
    generar_xfa,
)


@pytest.fixture
def pdf_simple(tmp_path: Path) -> Path:
    """Ruta a un PDF de 3 páginas generado al vuelo en un directorio temporal."""
    return generar_pdf_simple(tmp_path / "simple.pdf")


@pytest.fixture
def pdf_contenido(tmp_path: Path) -> Path:
    """PDF con índice, enlaces, texto buscable y metadatos (Fase 8)."""
    return generar_pdf_contenido(tmp_path / "contenido.pdf")


@pytest.fixture
def pdf_formulario(tmp_path: Path) -> Path:
    """PDF con un campo de cada tipo (texto, casilla, radio, combo, lista)."""
    return generar_formulario_completo(tmp_path / "formulario.pdf")


@pytest.fixture
def pdf_xfa(tmp_path: Path) -> Path:
    """PDF con entrada /XFA en el AcroForm."""
    return generar_xfa(tmp_path / "xfa.pdf")


@pytest.fixture
def certificado(tmp_path: Path) -> tuple[Path, Path, str]:
    """Genera un PKCS#12 de prueba. Devuelve (p12, cert_der, contraseña)."""
    p12, der = generar_pkcs12(tmp_path / "cert", contrasena="prueba")
    return p12, der, "prueba"
