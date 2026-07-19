"""Tests de MainWindow: apertura por diálogo/arrastre y aviso de errores."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import QDropEvent

from lectorpdf.ui import main_window as mw
from lectorpdf.ui.main_window import MainWindow, _ruta_pdf_de


def _pdf(tmp_path: Path, paginas: int = 3) -> Path:
    ruta = tmp_path / "doc.pdf"
    doc = fitz.open()
    for _ in range(paginas):
        doc.new_page()
    doc.save(ruta)
    doc.close()
    return ruta


def _mime_con_url(ruta: Path) -> QMimeData:
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(ruta))])
    return mime


# -- Helper de detección de PDF --------------------------------------------


def test_ruta_pdf_de_detecta_pdf_local(qapp: object, tmp_path: Path) -> None:
    ruta = tmp_path / "x.pdf"
    ruta.write_bytes(b"%PDF-1.7\n")

    assert _ruta_pdf_de(_mime_con_url(ruta)) == ruta


def test_ruta_pdf_de_ignora_no_pdf(qapp: object, tmp_path: Path) -> None:
    ruta = tmp_path / "x.txt"
    ruta.write_text("hola")

    assert _ruta_pdf_de(_mime_con_url(ruta)) is None


def test_ruta_pdf_de_sin_urls(qapp: object) -> None:
    assert _ruta_pdf_de(QMimeData()) is None


# -- Arrastrar y soltar -----------------------------------------------------


def test_soltar_pdf_abre_el_documento(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    ruta = _pdf(tmp_path, paginas=4)

    mime = _mime_con_url(ruta)  # se mantiene la referencia viva durante el drop
    evento = QDropEvent(
        QPointF(10, 10),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    ventana.dropEvent(evento)

    assert ventana._visor.documento is not None
    assert ventana._visor.documento.num_paginas == 4


# -- Aviso de error ---------------------------------------------------------


def test_abrir_ruta_con_aviso_devuelve_false_y_no_lanza(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    avisos: list[str] = []
    monkeypatch.setattr(
        mw.QMessageBox, "warning", lambda *a, **k: avisos.append(a[2])
    )
    ventana = MainWindow()

    ok = ventana.abrir_ruta_con_aviso(tmp_path / "no_existe.pdf")

    assert ok is False
    assert avisos  # se mostró un aviso, sin propagar la excepción


def test_abrir_ruta_con_aviso_devuelve_true_con_pdf_valido(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()

    ok = ventana.abrir_ruta_con_aviso(_pdf(tmp_path))

    assert ok is True
    assert ventana._visor.documento is not None
