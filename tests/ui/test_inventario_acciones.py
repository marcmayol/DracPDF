"""Inventario de acciones de la UI (cierre de la auditoría de integración).

Recorre las acciones de menú esperadas y comprueba que existen y están
conectadas; verifica los atajos declarados; y comprueba que las acciones
contextuales (Colocar/Cancelar del modo de colocación de firma) NO están visibles
fuera de su modo. Es la red de seguridad contra "goal cumplido con integración
incompleta": una acción que no exista o no esté conectada aquí, falla.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMenu

from lectorpdf.ui.main_window import MainWindow

# Acción esperada -> atajo (None = no se comprueba atajo, solo existencia+conexión).
_ESPERADAS: dict[str, str | None] = {
    # Archivo
    "Abrir…": "Ctrl+O",
    "Guardar": "Ctrl+S",
    "Guardar como…": "Ctrl+Shift+S",
    "Guardar una copia…": None,
    "Imprimir…": "Ctrl+P",
    "Vista previa de impresión…": None,
    "Restaurar sesión al arrancar": None,
    "Salir": "Ctrl+Q",
    # Edición
    "Deshacer": "Ctrl+Z",
    "Rehacer": "Ctrl+Y",
    "Copiar": "Ctrl+C",
    "Seleccionar todo": "Ctrl+E",
    "Añadir texto…": None,
    "Buscar…": "Ctrl+F",
    "Ir a página…": "Ctrl+G",
    # Ver
    "Una página": "Ctrl+1",
    "Doble página": "Ctrl+2",
    "Panel de miniaturas": "F7",
    "Índice del documento": "F8",
    "Ajustar a ancho": "Ctrl+3",
    "Ajustar a página": "Ctrl+4",
    "Rotar a la derecha": "Ctrl+Shift+R",
    "Rotar a la izquierda": "Ctrl+Shift+L",
    "Pantalla completa": "F11",
    "Claro": None,
    "Oscuro": None,
    # Documento
    "Unir PDF…": None,
    "Dividir PDF…": None,
    "Proteger con contraseña…": None,
    "Quitar contraseña…": None,
    "Comprimir…": None,
    "Exportar a PNG…": None,
    "Exportar a texto…": None,
    "Propiedades del documento…": None,
    # Documento → Convertir (salientes) y Archivo → Word a PDF (Fase 7)
    "A Word…": None,
    "A HTML…": None,
    "A Markdown…": None,
    "Convertir Word a PDF (reformateado)…": None,
    # Firmas
    "Firmar (dibujar y estampar)…": None,
    "Firmar con certificado…": None,
    "Verificar firmas…": None,
    # Ayuda
    "Acerca de DracPDF": None,
}


def _conectada(accion: object) -> bool:
    # Conectada por triggered (acciones normales) o toggled (conmutables).
    return (
        accion.receivers("2triggered()") > 0  # type: ignore[attr-defined]
        or accion.receivers("2toggled(bool)") > 0  # type: ignore[attr-defined]
    )


def _acciones_por_texto(ventana: MainWindow) -> dict[str, object]:
    resultado: dict[str, object] = {}

    def recorrer(menu: QMenu) -> None:
        for accion in menu.actions():
            if accion.text():
                resultado[accion.text()] = accion
            sub = accion.menu()
            if sub is not None:
                recorrer(sub)

    for m in ventana.menuBar().findChildren(QMenu):
        recorrer(m)
    return resultado


def test_todas_las_acciones_esperadas_existen_y_estan_conectadas(qapp: object) -> None:
    ventana = MainWindow()
    acciones = _acciones_por_texto(ventana)

    faltan = [t for t in _ESPERADAS if t not in acciones]
    assert not faltan, f"acciones ausentes del menú: {faltan}"

    for texto, atajo in _ESPERADAS.items():
        accion = acciones[texto]
        assert _conectada(accion), f"acción no conectada: {texto!r}"
        if atajo is not None:
            real = accion.shortcut().toString()  # type: ignore[attr-defined]
            assert real == atajo, f"{texto!r}: atajo {real!r} != {atajo!r}"


def test_presentacion_esta_deshabilitada(qapp: object) -> None:
    ventana = MainWindow()
    acciones = _acciones_por_texto(ventana)
    assert "Presentación" in acciones
    assert acciones["Presentación"].isEnabled() is False  # type: ignore[attr-defined]


def test_acciones_contextuales_ocultas_fuera_de_su_modo(qapp: object) -> None:
    ventana = MainWindow()
    # Colocar/Cancelar viven en la barra contextual de firma, oculta por defecto.
    assert ventana._barra_firma.isHidden()
    textos = {a.text() for a in ventana._barra_firma.actions()}
    assert "✓ Colocar" in textos and "✗ Cancelar" in textos
    assert ventana._accion_colocar.receivers("2triggered()") > 0
    assert ventana._accion_cancelar.receivers("2triggered()") > 0


def test_acciones_de_la_barra_de_herramientas_conectadas(qapp: object) -> None:
    ventana = MainWindow()
    for accion, _nombre in ventana._acciones_icono:
        assert _conectada(accion), f"botón de barra no conectado: {accion.toolTip()!r}"


def _pdf_min(tmp_path: Path) -> Path:
    import fitz

    ruta = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(ruta)
    doc.close()
    return ruta


def test_conversiones_salientes_deshabilitadas_sin_documento(
    qapp: object, tmp_path: Path
) -> None:
    from lectorpdf.ui import main_window as mw

    ventana = MainWindow()
    try:
        acciones = _acciones_por_texto(ventana)
        salientes = ("A Word…", "A HTML…", "A Markdown…")
        # Sin documento: las salientes deshabilitadas; Word→PDF (externo) habilitada.
        assert all(not acciones[t].isEnabled() for t in salientes)  # type: ignore[attr-defined]
        assert acciones["Convertir Word a PDF (reformateado)…"].isEnabled()  # type: ignore[attr-defined]

        # Con documento abierto: las salientes se habilitan.
        ventana.abrir_ruta(_pdf_min(tmp_path))
        acciones = _acciones_por_texto(ventana)
        assert all(acciones[t].isEnabled() for t in salientes)  # type: ignore[attr-defined]
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)


def test_anadir_texto_deshabilitado_sin_documento_o_firmado(
    qapp: object, tmp_path: Path
) -> None:
    from lectorpdf.adapters.pymupdf.registro import Marca
    from lectorpdf.ui import main_window as mw

    ventana = MainWindow()
    try:
        acciones = _acciones_por_texto(ventana)
        assert acciones["Añadir texto…"].isEnabled() is False  # type: ignore[attr-defined]

        doc = ventana.abrir_ruta(_pdf_min(tmp_path))
        assert acciones["Añadir texto…"].isEnabled() is True  # type: ignore[attr-defined]

        # Documento firmado: la edición de contenido se deshabilita.
        ventana._registro.marcar(doc.id, Marca.FIRMADO)
        ventana._actualizar_acciones_documento()
        assert acciones["Añadir texto…"].isEnabled() is False  # type: ignore[attr-defined]
    finally:
        ventana._prefs.remove(mw._CLAVE_RECIENTES)
