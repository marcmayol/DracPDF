"""Configuración común de los tests de UI.

Fuerza la plataforma `offscreen` de Qt (sin ventana real) y ofrece una única
QApplication para toda la sesión de tests.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="session")
def qapp() -> Iterator[QApplication]:
    app = QApplication.instance() or QApplication([])
    assert isinstance(app, QApplication)
    yield app


@pytest.fixture(autouse=True)
def _limpiar_stylesheet() -> Iterator[None]:
    """Evita que un test que aplica un tema deje el QSS puesto para los demás
    (el QSS altera tamaños mínimos y descuadraría tests de geometría)."""
    yield
    app = QApplication.instance()
    if isinstance(app, QApplication):
        app.setStyleSheet("")
