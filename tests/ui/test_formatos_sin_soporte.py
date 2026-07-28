"""Los formatos que no se convierten explican qué hacer, no fallan en silencio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.conversion import FORMATOS_SIN_SOPORTE
from lectorpdf.ui import main_window as mw
from lectorpdf.ui.main_window import MainWindow


def _doblar_seleccion(monkeypatch: pytest.MonkeyPatch, ruta: Path) -> list[str]:
    """Hace que el selector devuelva `ruta` y captura los avisos mostrados."""
    monkeypatch.setattr(
        mw.QFileDialog, "getOpenFileName", lambda *a, **k: (str(ruta), "")
    )
    avisos: list[str] = []
    monkeypatch.setattr(
        mw.QMessageBox,
        "information",
        lambda parent, titulo, texto, *a, **k: avisos.append(texto),
    )
    # Si el flujo continuara, pediría el destino: que falle el test si llega ahí.
    monkeypatch.setattr(
        mw.QFileDialog,
        "getSaveFileName",
        lambda *a, **k: pytest.fail("no debería pedir destino con un formato sin soporte"),
    )
    return avisos


@pytest.mark.parametrize("extension", sorted(FORMATOS_SIN_SOPORTE))
def test_desde_word_avisa_y_no_convierte(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, extension: str
) -> None:
    fichero = tmp_path / f"documento{extension}"
    fichero.write_bytes(b"contenido cualquiera")
    ventana = MainWindow()
    avisos = _doblar_seleccion(monkeypatch, fichero)

    ventana._convertir_word_a_pdf()

    assert len(avisos) == 1
    assert extension in avisos[0]


def test_desde_odt_avisa_con_un_doc(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fichero = tmp_path / "viejo.doc"
    fichero.write_bytes(b"contenido cualquiera")
    ventana = MainWindow()
    avisos = _doblar_seleccion(monkeypatch, fichero)

    ventana._convertir_texto_a_pdf("odt")

    assert len(avisos) == 1
    assert "guárdalo como .docx" in avisos[0]


def test_los_avisos_dicen_que_hacer(qapp: object) -> None:
    """Un aviso que solo diga "no compatible" no ayuda a nadie."""
    for extension, texto in FORMATOS_SIN_SOPORTE.items():
        assert extension in texto
        assert "Ábrelo" in texto or "Expórtalo" in texto
