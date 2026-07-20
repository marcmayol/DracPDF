"""Tests de la interfaz multi-documento con pestañas y de la restauración de
estado por documento y de sesión (Fase 8, tarea 9)."""

from __future__ import annotations

from pathlib import Path

import fitz

from lectorpdf.ui import main_window as mw
from lectorpdf.ui.main_window import MainWindow


def _pdf(ruta: Path, paginas: int = 3) -> Path:
    doc = fitz.open()
    for i in range(paginas):
        doc.new_page().insert_text((72, 72), f"P{i}", fontsize=18)
    doc.save(ruta)
    doc.close()
    return ruta


def _limpiar_prefs(ventana: MainWindow) -> None:
    ventana._prefs.remove("estado")
    ventana._prefs.remove(mw._CLAVE_RECIENTES)
    ventana._prefs.remove("sesion")


def test_abrir_dos_documentos_crea_dos_pestanas(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(_pdf(tmp_path / "a.pdf", 2))
        ventana.abrir_ruta(_pdf(tmp_path / "b.pdf", 3))

        assert ventana._pestanas.count() == 2
        rutas = {v.documento.ruta.name for v in ventana._vistas() if v.documento}
        assert rutas == {"a.pdf", "b.pdf"}
    finally:
        _limpiar_prefs(ventana)


def test_reabrir_el_mismo_activa_su_pestana(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    try:
        a = _pdf(tmp_path / "a.pdf", 2)
        ventana.abrir_ruta(a)
        ventana.abrir_ruta(_pdf(tmp_path / "b.pdf", 3))  # b activa
        assert ventana._documento is not None and ventana._documento.ruta.name == "b.pdf"

        ventana.abrir_ruta(a)  # ya abierto: activa su pestaña, no duplica

        assert ventana._pestanas.count() == 2
        assert ventana._documento is not None
        assert ventana._documento.ruta.name == "a.pdf"
    finally:
        _limpiar_prefs(ventana)


def test_primera_apertura_reutiliza_la_pestana_vacia(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    try:
        assert ventana._pestanas.count() == 1  # pestaña vacía inicial
        ventana.abrir_ruta(_pdf(tmp_path / "a.pdf", 2))
        assert ventana._pestanas.count() == 1  # se reutilizó, no se añadió otra
    finally:
        _limpiar_prefs(ventana)


def test_pagina_y_zoom_persisten_por_documento(qapp: object, tmp_path: Path) -> None:
    ruta = _pdf(tmp_path / "a.pdf", 6)
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(ruta)
        ventana._visor.ir_a_pagina(3)
        ventana._visor.set_escala(2.0)
        ventana._guardar_estado_documento(ventana._documento, ventana._vista())

        otra = MainWindow()
        try:
            otra.abrir_ruta(ruta)
            assert otra._visor.pagina_actual() == 3
            assert otra._visor.escala == 2.0
        finally:
            _limpiar_prefs(otra)
    finally:
        _limpiar_prefs(ventana)


def test_restaurar_sesion_reabre_los_documentos(qapp: object, tmp_path: Path) -> None:
    a = _pdf(tmp_path / "a.pdf", 2)
    b = _pdf(tmp_path / "b.pdf", 3)
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(a)
        ventana.abrir_ruta(b)
        ventana._guardar_sesion()

        restaurada = MainWindow(restaurar_sesion=True)
        try:
            nombres = {
                v.documento.ruta.name for v in restaurada._vistas() if v.documento
            }
            assert nombres == {"a.pdf", "b.pdf"}
        finally:
            _limpiar_prefs(restaurada)
    finally:
        _limpiar_prefs(ventana)


def test_restaurar_sesion_omite_rutas_inexistentes(
    qapp: object, tmp_path: Path
) -> None:
    a = _pdf(tmp_path / "a.pdf", 2)
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(a)
        # Sesión con una ruta válida y otra que ya no existe.
        ventana._prefs.setValue(
            mw._CLAVE_SESION, [str(a), str(tmp_path / "fantasma.pdf")]
        )

        restaurada = MainWindow(restaurar_sesion=True)
        try:
            nombres = [
                v.documento.ruta.name for v in restaurada._vistas() if v.documento
            ]
            assert nombres == ["a.pdf"]  # la inexistente se omite en silencio
        finally:
            _limpiar_prefs(restaurada)
    finally:
        _limpiar_prefs(ventana)
