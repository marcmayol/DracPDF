"""Regresión de persistencia de preferencias entre sesiones (Fase 5).

Verifica que el tema (y las demás preferencias que comparten mecanismo) sobrevive
a un reinicio: se conmuta, se simula el cierre y se crea una ventana nueva con el
MISMO almacén de QSettings, que debe arrancar con lo guardado y no con un defecto
fijo. Todas las preferencias usan un único QSettings(AJUSTES_ORG, AJUSTES_APP).

El fixture aísla el almacén real (snapshot + restauración) para no pisar las
preferencias del usuario en la máquina donde corren los tests.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import fitz
import pytest
from PySide6.QtCore import QSettings

from lectorpdf.ui.main_window import MainWindow
from lectorpdf.ui.theme.estilos import (
    AJUSTES_APP,
    AJUSTES_ORG,
    guardar_preferencia_tema,
)


@pytest.fixture
def ajustes_aislados() -> Iterator[QSettings]:
    """Aísla el almacén real: lo vacía para el test y lo restaura al terminar."""
    s = QSettings(AJUSTES_ORG, AJUSTES_APP)
    snapshot = {k: s.value(k) for k in s.allKeys()}
    s.clear()
    s.sync()
    yield s
    s.clear()
    for clave, valor in snapshot.items():
        s.setValue(clave, valor)
    s.sync()


def _pdf(tmp_path: Path, paginas: int = 5) -> Path:
    ruta = tmp_path / "doc.pdf"
    doc = fitz.open()
    for _ in range(paginas):
        doc.new_page()
    doc.save(ruta)
    doc.close()
    return ruta


def test_tema_persiste_tras_reiniciar(qapp: object, ajustes_aislados: QSettings) -> None:
    guardar_preferencia_tema("claro")
    w1 = MainWindow(restaurar_sesion=False, persistir_sesion=False)
    assert w1._tema.nombre == "claro"
    # Conmuta a oscuro como un clic del usuario (dispara la acción del menú Ver).
    w1._accion_tema_oscuro.trigger()
    assert w1._tema.nombre == "oscuro"
    w1.close()

    # "Reinicio": una ventana nueva con el mismo almacén debe arrancar en oscuro.
    w2 = MainWindow(restaurar_sesion=False, persistir_sesion=False)
    assert w2._tema.nombre == "oscuro"
    w2.close()


def test_arranque_aplica_el_tema_guardado_no_un_defecto(
    qapp: object, ajustes_aislados: QSettings
) -> None:
    ajustes_aislados.setValue("ui/tema", "oscuro")
    ajustes_aislados.sync()

    w = MainWindow(restaurar_sesion=False, persistir_sesion=False)
    assert w._tema.nombre == "oscuro"  # lee QSettings antes de aplicar, no fija claro
    w.close()


def test_preferencias_comparten_un_unico_almacen(
    qapp: object, ajustes_aislados: QSettings
) -> None:
    # Tema y recientes se escriben en el MISMO QSettings(org, app) que lee la app.
    ajustes_aislados.setValue("ui/tema", "oscuro")
    ajustes_aislados.setValue("archivo/recientes", ["/docs/a.pdf"])
    ajustes_aislados.sync()

    w = MainWindow(restaurar_sesion=False, persistir_sesion=False)
    assert w._tema.nombre == "oscuro"
    assert w._recientes() == ["/docs/a.pdf"]
    assert w._prefs.organizationName() == AJUSTES_ORG
    assert w._prefs.applicationName() == AJUSTES_APP
    w.close()


def test_estado_por_documento_pagina_y_zoom_persiste(
    qapp: object, ajustes_aislados: QSettings, tmp_path: Path
) -> None:
    ruta = _pdf(tmp_path, paginas=5)
    w1 = MainWindow(restaurar_sesion=False, persistir_sesion=False)
    w1.abrir_ruta(ruta)
    w1._visor.set_escala(1.5)
    w1._visor.ir_a_pagina(3)
    w1._cerrar_pestana(w1._pestanas.currentIndex())  # guarda estado del documento
    w1.close()

    w2 = MainWindow(restaurar_sesion=False, persistir_sesion=False)
    w2.abrir_ruta(ruta)
    assert w2._visor.escala == 1.5
    assert w2._visor.pagina_actual() == 3
    w2.close()
