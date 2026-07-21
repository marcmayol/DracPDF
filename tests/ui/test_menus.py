"""Tests de la barra de menús del diseño Ladón (estructura y acciones)."""

from __future__ import annotations

from PySide6.QtWidgets import QMenu

from lectorpdf.ui.main_window import MainWindow


def _textos_de_menu(ventana: MainWindow, nombre: str) -> list[str]:
    """Textos de todas las acciones del menú `nombre` y sus submenús.

    Mantiene vivas las acciones de la barra (evita que shiboken invalide los
    wrappers de los submenús) recorriéndolo todo mientras `ventana` existe."""
    submenus = {
        m.title(): m for m in ventana.menuBar().findChildren(QMenu) if m.title()
    }
    objetivo = submenus.get(nombre)
    assert objetivo is not None, f"No existe el menú {nombre!r}"

    textos: list[str] = []

    def recorrer(menu: QMenu) -> None:
        for accion in menu.actions():
            if accion.text():
                textos.append(accion.text())
            sub = accion.menu()
            if sub is not None:
                recorrer(sub)

    recorrer(objetivo)
    return textos


def test_barra_de_menus_del_diseno(qapp: object) -> None:
    ventana = MainWindow()
    nombres = [a.text() for a in ventana.menuBar().actions() if a.text()]
    assert nombres == ["Archivo", "Edición", "Ver", "Documento", "Firmas", "Ayuda"]
    assert "Herramientas" not in nombres


def test_documento_agrupa_las_operaciones_de_pdf(qapp: object) -> None:
    ventana = MainWindow()
    textos = _textos_de_menu(ventana, "Documento")
    for esperado in ("Unir PDF…", "Dividir PDF…", "Comprimir…", "Exportar a PNG…"):
        assert esperado in textos
    assert "Propiedades del documento…" in textos  # movido aquí desde Archivo


def test_edicion_y_ver_tienen_las_acciones_clave(qapp: object) -> None:
    ventana = MainWindow()
    edicion = _textos_de_menu(ventana, "Edición")
    for esperado in ("Deshacer", "Rehacer", "Copiar", "Seleccionar todo", "Buscar…"):
        assert esperado in edicion

    ver = _textos_de_menu(ventana, "Ver")
    for esperado in (
        "Una página",
        "Doble página",
        "Ajustar a ancho",
        "Ajustar a página",
        "Rotar a la derecha",
        "Rotar a la izquierda",
        "Pantalla completa",
        "Claro",
        "Oscuro",
    ):
        assert esperado in ver


def test_firmas_y_ayuda(qapp: object) -> None:
    ventana = MainWindow()
    firmas = _textos_de_menu(ventana, "Firmas")
    assert any("certificado" in t for t in firmas)
    assert any("Verificar" in t for t in firmas)

    ayuda = _textos_de_menu(ventana, "Ayuda")
    assert any("Acerca de" in t for t in ayuda)
