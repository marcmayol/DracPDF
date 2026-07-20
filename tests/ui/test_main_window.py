"""Tests de MainWindow: apertura por diálogo/arrastre y aviso de errores."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import QCloseEvent, QDropEvent
from PySide6.QtWidgets import QLineEdit, QMessageBox

from lectorpdf.ui import main_window as mw
from lectorpdf.ui.main_window import MainWindow, _ruta_pdf_de
from tests.adapters.generar_fixtures import generar_pdf_contenido
from tests.adapters.generar_fixtures_formularios import (
    generar_formulario_completo,
    generar_xfa,
)


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


# -- Búsqueda (Fase 8) ------------------------------------------------------


def test_buscar_encuentra_navega_y_resalta(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    ventana.abrir_ruta(generar_pdf_contenido(tmp_path / "contenido.pdf"))

    ventana._ejecutar_busqueda("Ladon", False)

    assert len(ventana._coincidencias) == 3
    assert ventana._indice_coincidencia == 0
    assert len(ventana._capa_busqueda.items()) == 3

    # F3 avanza cíclicamente y actualiza el contador.
    ventana._busqueda_siguiente()
    assert ventana._indice_coincidencia == 1
    ventana._busqueda_anterior()
    ventana._busqueda_anterior()
    assert ventana._indice_coincidencia == 2  # da la vuelta (0 -> 2)


def test_cerrar_busqueda_limpia_estado_y_resaltados(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    ventana.abrir_ruta(generar_pdf_contenido(tmp_path / "contenido.pdf"))
    ventana._ejecutar_busqueda("Ladon", False)

    ventana._cerrar_busqueda()

    assert ventana._coincidencias == ()
    assert ventana._capa_busqueda.items() == []
    assert ventana._barra_busqueda.isHidden()


def test_seleccionar_rango_conocido_copia_ese_texto(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    documento = ventana.abrir_ruta(generar_pdf_contenido(tmp_path / "contenido.pdf"))

    palabras = ventana._obtener_palabras.ejecutar(documento, 0)
    textos = [p.texto for p in palabras]
    i = textos.index("frase")  # "frase exacta seleccionable"
    inicio, fin = palabras[i].rect_pt, palabras[i + 2].rect_pt

    capa = ventana._capa_seleccion
    capa._iniciar_arrastre(0, (inicio.x0 + inicio.x1) / 2, (inicio.y0 + inicio.y1) / 2)
    capa._extender_arrastre((fin.x0 + fin.x1) / 2, (fin.y0 + fin.y1) / 2)

    assert capa.copiar() == "frase exacta seleccionable"


# -- Índice / outline (Fase 8) ----------------------------------------------


def test_indice_visible_y_navega_con_outline(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    ventana.abrir_ruta(generar_pdf_contenido(tmp_path / "contenido.pdf"))

    assert ventana._panel_lateral.isTabVisible(ventana._idx_tab_indice)
    assert ventana._outline.topLevelItemCount() == 3  # Portada, Desarrollo, Cierre

    ventana._outline._al_pulsar(ventana._outline.topLevelItem(1), 0)  # Desarrollo->1
    assert ventana._visor.pagina_actual() == 1


def test_pestana_indice_oculta_sin_outline(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    ventana.abrir_ruta(_pdf(tmp_path))  # PDF sin índice

    assert not ventana._panel_lateral.isTabVisible(ventana._idx_tab_indice)


# -- Enlaces e ir a página (Fase 8) -----------------------------------------


def test_enlace_interno_navega(qapp: object, tmp_path: Path) -> None:
    from lectorpdf.core.domain.contenido import Enlace
    from lectorpdf.core.domain.formularios import RectanguloPt

    ventana = MainWindow()
    ventana.abrir_ruta(generar_pdf_contenido(tmp_path / "contenido.pdf"))

    ventana._capa_enlaces._activar(Enlace(RectanguloPt(0, 0, 1, 1), pagina_destino=2))

    assert ventana._visor.pagina_actual() == 2


def test_enlace_externo_confirma_y_abre(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lectorpdf.core.domain.contenido import Enlace
    from lectorpdf.core.domain.formularios import RectanguloPt

    ventana = MainWindow()
    ventana.abrir_ruta(generar_pdf_contenido(tmp_path / "contenido.pdf"))

    monkeypatch.setattr(
        mw.QMessageBox,
        "question",
        lambda *a, **k: mw.QMessageBox.StandardButton.Open,
    )
    abiertas: list[str] = []
    monkeypatch.setattr(
        mw.QDesktopServices, "openUrl", lambda url: abiertas.append(url.toString())
    )

    ventana._capa_enlaces._activar(
        Enlace(RectanguloPt(0, 0, 1, 1), uri="https://example.com/")
    )

    assert abiertas == ["https://example.com/"]


def test_ir_a_pagina_dialogo(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ventana = MainWindow()
    ventana.abrir_ruta(_pdf(tmp_path, paginas=5))

    monkeypatch.setattr(mw.QInputDialog, "getInt", lambda *a, **k: (3, True))
    ventana._ir_a_pagina_dialogo()

    assert ventana._visor.pagina_actual() == 2  # página 3 (1-based) -> índice 2


def test_imprimir_desde_la_ventana_produce_pdf(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtPrintSupport import QPrinter
    from PySide6.QtWidgets import QDialog

    ventana = MainWindow()
    ventana.abrir_ruta(_pdf(tmp_path, paginas=3))
    salida = tmp_path / "impreso.pdf"

    class _DialogoFalso:
        def __init__(self, printer: QPrinter, parent: object) -> None:
            self._printer = printer
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(str(salida))
            printer.setResolution(150)

        def setOption(self, *a: object, **k: object) -> None:
            pass

        def exec(self) -> int:
            self._printer.setFromTo(1, 3)
            return QDialog.DialogCode.Accepted

    monkeypatch.setattr(mw, "QPrintDialog", _DialogoFalso)
    ventana._imprimir()

    assert salida.exists()
    doc = fitz.open(salida)
    assert doc.page_count == 3
    doc.close()


# -- Modos de vista (Fase 8) ------------------------------------------------


def test_conmutar_doble_actualiza_visor_y_prefs(qapp: object) -> None:
    ventana = MainWindow()
    try:
        ventana._conmutar_doble(True)
        assert ventana._visor.doble_pagina() is True
        assert ventana._prefs.value(mw._CLAVE_DOBLE, type=bool) is True
    finally:
        ventana._prefs.setValue(mw._CLAVE_DOBLE, False)


def test_modo_ajuste_se_persiste(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(_pdf(tmp_path))
        ventana._visor.ajustar_a_ancho()
        assert ventana._prefs.value(mw._CLAVE_MODO_AJUSTE) == "ANCHO"
    finally:
        ventana._prefs.setValue(mw._CLAVE_MODO_AJUSTE, "LIBRE")


# -- Menú Archivo: recientes, guardar como/copia, banda firmado (Fase 8) ----


def test_abrir_registra_reciente(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    try:
        ruta = _pdf(tmp_path)
        ventana.abrir_ruta(ruta)
        assert str(ruta) in ventana._recientes()
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_guardar_como_cambia_de_documento(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(_pdf(tmp_path, paginas=2))
        destino = tmp_path / "otro.pdf"
        monkeypatch.setattr(
            mw.QFileDialog, "getSaveFileName", lambda *a, **k: (str(destino), "")
        )

        ventana._guardar_como()

        assert destino.exists()
        assert ventana._documento is not None
        assert ventana._documento.ruta == destino
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_guardar_copia_no_cambia_documento(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ventana = MainWindow()
    try:
        origen = _pdf(tmp_path, paginas=2)
        ventana.abrir_ruta(origen)
        copia = tmp_path / "copia.pdf"
        monkeypatch.setattr(
            mw.QFileDialog, "getSaveFileName", lambda *a, **k: (str(copia), "")
        )
        monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

        ventana._guardar_copia()

        assert copia.exists()
        assert ventana._documento is not None
        assert ventana._documento.ruta == origen  # sigue en el original
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_banda_firmado_visible_para_documento_firmado(
    qapp: object, tmp_path: Path
) -> None:
    from lectorpdf.adapters.pymupdf.registro import Marca

    ventana = MainWindow()
    try:
        documento = ventana.abrir_ruta(_pdf(tmp_path))
        assert ventana._banda_firmado.isHidden()  # no firmado al abrir

        ventana._registro.marcar(documento.id, Marca.FIRMADO)
        ventana._actualizar_banda_firmado()

        assert not ventana._banda_firmado.isHidden()
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


# -- Formularios ------------------------------------------------------------


def _lineedit_de(ventana: MainWindow) -> QLineEdit:
    for proxy in ventana._capa_form.proxies().values():
        widget = proxy.widget()
        if isinstance(widget, QLineEdit) and widget.isEnabled():
            return widget
    raise AssertionError("No hay QLineEdit editable en el overlay")


def test_abrir_formulario_carga_campos_en_el_overlay(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    ventana.resize(900, 700)
    ventana.show()

    ventana.abrir_ruta(generar_formulario_completo(tmp_path / "f.pdf"))

    # La primera página es visible: sus campos deben tener proxy.
    assert ventana._capa_form.proxies()


def test_abrir_xfa_muestra_aviso_y_no_carga_campos(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    avisos: list[str] = []
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *a, **k: avisos.append(a[1]))
    ventana = MainWindow()
    ventana.resize(900, 700)
    ventana.show()

    ventana.abrir_ruta(generar_xfa(tmp_path / "x.pdf"))

    assert avisos  # se mostró el aviso XFA
    assert ventana._capa_form.proxies() == {}


def test_guardar_limpia_los_cambios(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    ventana.resize(900, 700)
    ventana.show()
    ventana.abrir_ruta(generar_formulario_completo(tmp_path / "f.pdf"))
    documento = ventana._documento
    assert documento is not None

    editor = _lineedit_de(ventana)
    editor.setText("Marc")
    editor.editingFinished.emit()
    assert ventana._guardar_form.hay_cambios_sin_guardar(documento) is True

    ventana._guardar()

    assert ventana._guardar_form.hay_cambios_sin_guardar(documento) is False


def test_organizar_eliminar_pagina_actualiza_el_documento(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    ventana.resize(900, 700)
    ventana.show()
    ventana.abrir_ruta(_pdf(tmp_path, paginas=4))
    assert ventana._documento is not None and ventana._documento.num_paginas == 4

    ventana._miniaturas.eliminar_solicitado.emit(1)

    assert ventana._documento.num_paginas == 3


def test_organizar_documento_firmado_avisa(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    avisos: list[str] = []
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *a, **k: avisos.append(a[1]))
    ventana = MainWindow()
    ventana.resize(900, 700)
    ventana.show()
    ventana.abrir_ruta(_pdf(tmp_path, paginas=3))
    documento = ventana._documento
    assert documento is not None
    ventana._registro.marcar(documento.id, mw_marca().FIRMADO)

    ventana._miniaturas.rotar_solicitado.emit(0, 90)

    assert avisos  # se avisó y no se organizó
    assert ventana._documento.num_paginas == 3


def mw_marca():  # type: ignore[no-untyped-def]
    from lectorpdf.adapters.pymupdf.registro import Marca

    return Marca


def test_firmar_estampa_y_marca_cambios_sin_guardar(
    qapp: object, tmp_path: Path
) -> None:
    import fitz as _fitz

    ventana = MainWindow()
    ventana.resize(900, 700)
    ventana.show()
    ventana.abrir_ruta(_pdf(tmp_path, paginas=2))
    documento = ventana._documento
    assert documento is not None

    png = _fitz.Pixmap(
        _fitz.csRGB, _fitz.IRect(0, 0, 100, 40), False
    ).tobytes("png")
    ventana._capa_firma.iniciar_colocacion(documento, png)
    ventana._confirmar_firma()

    assert ventana._guardar_form.hay_cambios_sin_guardar(documento) is True


def test_cerrar_con_cambios_guarda_si_el_usuario_lo_pide(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        mw.QMessageBox,
        "question",
        lambda *a, **k: QMessageBox.StandardButton.Save,
    )
    ventana = MainWindow()
    ventana.resize(900, 700)
    ventana.show()
    ventana.abrir_ruta(generar_formulario_completo(tmp_path / "f.pdf"))
    documento = ventana._documento
    assert documento is not None

    editor = _lineedit_de(ventana)
    editor.setText("Marc")
    editor.editingFinished.emit()

    evento = QCloseEvent()
    ventana.closeEvent(evento)

    assert ventana._guardar_form.hay_cambios_sin_guardar(documento) is False
    assert evento.isAccepted()


def test_abrir_desde_instancia_abre_el_documento(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    try:
        ruta = _pdf(tmp_path)
        ventana.abrir_desde_instancia(str(ruta))
        assert ventana._documento is not None
        assert ventana._documento.ruta == ruta
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)
