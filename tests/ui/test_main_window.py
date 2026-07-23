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


def test_deshacer_tras_editar_dos_campos_restaura_en_orden(
    qapp: object, tmp_path: Path
) -> None:
    from tests.adapters.generar_fixtures_formularios import (
        generar_formulario_dos_textos,
    )

    ventana = MainWindow()
    try:
        doc = ventana.abrir_ruta(generar_formulario_dos_textos(tmp_path / "dos.pdf"))
        campos = ventana._listar.ejecutar(doc)
        a = next(c for c in campos if c.nombre == "a")
        b = next(c for c in campos if c.nombre == "b")

        ventana._rellenar.ejecutar(doc, a, "Marc")
        ventana._rellenar.ejecutar(doc, b, "Mayol")

        def valor(campo_id: str) -> str:
            return next(
                c.valor for c in ventana._listar.ejecutar(doc) if c.id == campo_id
            )

        ventana._deshacer()  # deshace el segundo campo
        assert valor(b.id) == "Y"
        assert valor(a.id) == "Marc"
        ventana._deshacer()  # deshace el primero
        assert valor(a.id) == "X"
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


# -- Menú contextual y atajos (Fase 8, tarea 13) ----------------------------


def test_menu_contextual_tiene_las_acciones(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(_pdf(tmp_path))
        menu = ventana._construir_menu_contextual(ventana._vista())
        textos = [a.text() for a in menu.actions() if a.text()]
        for esperado in (
            "Copiar",
            "Seleccionar todo",
            "Buscar…",
            "Ir a página…",
            "Rotar a la izquierda",
            "Imprimir…",
            "Propiedades del documento…",
        ):
            assert esperado in textos
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_copiar_del_menu_deshabilitado_sin_seleccion(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(_pdf(tmp_path))
        menu = ventana._construir_menu_contextual(ventana._vista())
        copiar = next(a for a in menu.actions() if a.text() == "Copiar")
        assert copiar.isEnabled() is False  # no hay texto seleccionado
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_cerrar_pestana_actual_deja_una_vacia(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(_pdf(tmp_path))
        ventana._cerrar_pestana_actual()
        # Se cierra la única pestaña; queda una vacía (siempre >= 1).
        assert ventana._pestanas.count() == 1
        assert ventana._documento is None
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_barra_firma_es_contextual_del_modo_colocacion(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(_pdf(tmp_path, paginas=2))
        doc = ventana._documento
        assert doc is not None

        # Oculta por defecto (fuera del modo colocación).
        assert ventana._barra_firma.isHidden()

        png = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 40), False).tobytes("png")
        ventana._capa_firma.iniciar_colocacion(doc, png)
        ventana._actualizar_controles_firma()
        assert not ventana._barra_firma.isHidden()  # visible al colocar

        ventana._cancelar_colocacion()
        assert ventana._barra_firma.isHidden()  # vuelve a ocultarse
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_toggles_de_paneles_muestran_y_ocultan_el_dock(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(_pdf(tmp_path))
        ventana._dock_navegacion.show()
        ventana._panel_lateral.setCurrentWidget(ventana._miniaturas)
        ventana._sincronizar_checks_paneles()

        # Con el dock visible en Miniaturas: solo esa acción marcada.
        assert ventana._accion_panel_miniaturas.isChecked() is True
        assert ventana._accion_panel_indice.isChecked() is False

        # F8 lleva a Índice: cambia la marca (mutuamente excluyentes).
        ventana._accion_panel_indice.trigger()
        assert ventana._accion_panel_indice.isChecked() is True
        assert ventana._accion_panel_miniaturas.isChecked() is False

        # Desmarcar oculta el dock; ninguna acción marcada.
        ventana._accion_panel_indice.trigger()
        assert ventana._dock_navegacion.isHidden()
        assert ventana._accion_panel_miniaturas.isChecked() is False
        assert ventana._accion_panel_indice.isChecked() is False
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


# -- Conversiones de formato (Fase 7) ---------------------------------------


def test_convertir_deshabilitado_sin_documento_y_habilitado_al_abrir(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    try:
        assert ventana._accion_convertir_word.isEnabled() is False
        assert ventana._accion_convertir_html.isEnabled() is False
        assert ventana._accion_convertir_md.isEnabled() is False

        ventana.abrir_ruta(_pdf(tmp_path))
        assert ventana._accion_convertir_word.isEnabled() is True
        assert ventana._accion_convertir_md.isEnabled() is True
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_convertir_a_markdown_produce_fichero(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(generar_pdf_contenido(tmp_path / "contenido.pdf"))
        destino = tmp_path / "salida.md"

        class _DialogoFalso:
            def __init__(self, *a: object, **k: object) -> None:
                pass

            def exec(self) -> int:
                from PySide6.QtWidgets import QDialog

                return QDialog.DialogCode.Accepted

            def rango(self) -> None:
                return None

            def imagenes_embebidas(self) -> bool:
                return True

        monkeypatch.setattr(mw, "ConversionSalienteDialog", _DialogoFalso)
        monkeypatch.setattr(
            mw.QFileDialog, "getSaveFileName", lambda *a, **k: (str(destino), "")
        )
        monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

        ventana._convertir_a_markdown()

        assert destino.is_file()
        assert "Ladon" in destino.read_text(encoding="utf-8")
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_convertir_word_a_pdf_produce_pdf(
    qapp: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.adapters.generar_fixtures_docx import generar_docx_prueba

    ventana = MainWindow()
    try:
        docx = generar_docx_prueba(tmp_path / "prueba.docx")
        destino = tmp_path / "salida.pdf"

        monkeypatch.setattr(
            mw.QFileDialog, "getOpenFileName", lambda *a, **k: (str(docx), "")
        )
        monkeypatch.setattr(
            mw.QFileDialog, "getSaveFileName", lambda *a, **k: (str(destino), "")
        )
        monkeypatch.setattr(
            mw.ConversionWordDialog,
            "exec",
            lambda self: __import__(
                "PySide6.QtWidgets", fromlist=["QDialog"]
            ).QDialog.DialogCode.Accepted,
        )
        # No abrir el PDF resultante al terminar.
        monkeypatch.setattr(
            mw.QMessageBox,
            "question",
            lambda *a, **k: mw.QMessageBox.StandardButton.No,
        )

        ventana._convertir_word_a_pdf()

        assert destino.is_file()
        doc = fitz.open(destino)
        assert doc.page_count >= 1
        doc.close()
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


# -- Conformidad Ladón: control de página y zoom en la toolbar --------------


def test_control_pagina_navega_al_escribir(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(_pdf(tmp_path, paginas=8))
        # El control refleja la página actual y su total.
        assert ventana._control_pagina._etiqueta_total.text() == "/ 8"
        # Escribir un número navega a esa página.
        ventana._control_pagina._campo.setText("5")
        ventana._control_pagina._campo.editingFinished.emit()
        assert ventana._visor.pagina_actual() == 4
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_control_zoom_ajusta_escala_al_escribir(qapp: object, tmp_path: Path) -> None:
    ventana = MainWindow()
    try:
        ventana.abrir_ruta(_pdf(tmp_path, paginas=2))
        # Escribir un porcentaje fija la escala del visor.
        ventana._control_zoom._campo.setText("150")
        ventana._control_zoom._campo.editingFinished.emit()
        assert ventana._visor.escala == 1.5
        # Y un cambio de zoom del visor se refleja en el control.
        ventana._visor.set_escala(0.75)
        assert ventana._control_zoom._campo.text() == "75"
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def _texto_pagina(ventana: MainWindow, doc_id: str) -> str:
    return ventana._registro.obtener(doc_id)[0].get_text().replace("\xa0", " ")


def test_deshacer_desde_menu_revierte_texto_anadido(
    qapp: object, tmp_path: Path
) -> None:
    from lectorpdf.core.domain.anotaciones import FuenteTexto, TextoNuevo
    from lectorpdf.core.domain.formularios import RectanguloPt

    ventana = MainWindow()
    try:
        doc = ventana.abrir_ruta(_pdf(tmp_path, paginas=1))
        texto = TextoNuevo(
            RectanguloPt(40, 40, 300, 90),
            "Texto de prueba",
            FuenteTexto.SANS,
            14.0,
            (0.0, 0.0, 0.0),
        )
        ventana._anadir_texto.ejecutar(doc, 0, texto)
        assert "Texto de prueba" in _texto_pagina(ventana, doc.id)

        ventana._deshacer()  # desde el handler del menú Edición
        assert "Texto de prueba" not in _texto_pagina(ventana, doc.id)

        ventana._rehacer()
        assert "Texto de prueba" in _texto_pagina(ventana, doc.id)
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_corregir_texto_desde_handler_elimina_original(
    qapp: object, tmp_path: Path
) -> None:
    from lectorpdf.core.domain.anotaciones import FuenteTexto
    from lectorpdf.core.domain.formularios import RectanguloPt

    ruta = tmp_path / "c.pdf"
    d = fitz.open()
    d.new_page().insert_text((40, 90), "El total es MIL pesetas", fontsize=13)
    d.save(ruta)
    d.close()

    ventana = MainWindow()
    try:
        doc = ventana.abrir_ruta(ruta)
        r = ventana._registro.obtener(doc.id)[0].search_for("MIL")[0]
        rect = RectanguloPt(r.x0, r.y0, r.x1, r.y1)
        ventana._ejecutar_correccion(doc, 0, rect, "DOS", FuenteTexto.SERIF)
        texto = ventana._registro.obtener(doc.id)[0].get_text()
        assert "MIL" not in texto
        assert "DOS" in texto
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_marcar_seleccion_y_deshacer_desde_menu(
    qapp: object, tmp_path: Path
) -> None:
    from lectorpdf.core.domain.anotaciones import TipoMarcado

    ventana = MainWindow()
    try:
        doc = ventana.abrir_ruta(generar_pdf_contenido(tmp_path / "c.pdf"))
        ventana._vista().capa_seleccion.seleccionar_todo(0)
        ventana._marcar_seleccion(TipoMarcado.RESALTADO)
        page = ventana._registro.obtener(doc.id)[0]
        assert len(list(page.annots())) >= 1

        ventana._deshacer()  # desde el handler del menú Edición
        assert len(list(ventana._registro.obtener(doc.id)[0].annots())) == 0
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_estado_vacio_al_arrancar_y_paneles_ocultos(qapp: object) -> None:
    ventana = MainWindow()
    try:
        # Sin documento: se muestra el estado vacío y los paneles laterales
        # quedan ocultos (no hay pestaña "Sin documento" visible).
        assert ventana._central.currentWidget() is ventana._estado_vacio
        assert ventana._dock_navegacion.isVisible() is False
        assert ventana._dock_verificacion.isVisible() is False
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_abrir_muestra_pestanas_y_cerrar_vuelve_al_estado_vacio(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    ventana.show()
    try:
        ventana.abrir_ruta(_pdf(tmp_path, paginas=2))
        assert ventana._central.currentWidget() is ventana._pestanas
        assert ventana._dock_navegacion.isVisible() is True
        # Cerrar la última pestaña vuelve al estado vacío.
        ventana._cerrar_pestana(ventana._pestanas.currentIndex())
        assert ventana._central.currentWidget() is ventana._estado_vacio
        assert ventana._dock_navegacion.isVisible() is False
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_barra_estado_refleja_documento_y_zoom(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    try:
        # Sin documento la barra de estado está vacía.
        assert ventana._estado_nombre.text() == ""
        assert ventana._estado_zoom.text() == ""
        ventana.abrir_ruta(_pdf(tmp_path, paginas=7))
        assert ventana._estado_nombre.text() == "doc.pdf"
        assert ventana._estado_paginas.text() == "7 páginas"
        # El zoom se refleja y se actualiza al cambiarlo.
        ventana._visor.set_escala(1.25)
        assert ventana._estado_zoom.text() == "125 %"
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_boton_firmar_destacado_con_objectname(qapp: object) -> None:
    # El botón "Firmar con certificado" lleva objectName para el QSS de acento.
    ventana = MainWindow()
    try:
        barra = ventana.findChildren(mw.QToolBar)[0]
        boton = barra.widgetForAction(ventana._accion_firmar)
        assert boton is not None
        assert boton.objectName() == "botonFirmar"
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_boton_formulario_se_habilita_solo_con_campos(
    qapp: object, tmp_path: Path
) -> None:
    ventana = MainWindow()
    try:
        assert ventana._accion_form.isEnabled() is False  # sin documento
        ventana.abrir_ruta(_pdf(tmp_path, paginas=2))  # PDF sin campos
        assert ventana._accion_form.isEnabled() is False
        ventana.abrir_ruta(generar_formulario_completo(tmp_path / "f.pdf"))
        assert ventana._accion_form.isEnabled() is True
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)
