"""La barra de herramientas y los iconos que usa, según la maqueta Ladón 11b."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.recursos import base_recursos
from lectorpdf.ui.main_window import MainWindow

_DIR_ICONOS = base_recursos() / "assets" / "icons"


def test_la_barra_lleva_abrir_guardar_buscar_e_imprimir(qapp: object) -> None:
    ventana = MainWindow()

    nombres = [nombre for _accion, nombre in ventana._acciones_icono]

    assert nombres[:4] == ["open", "save", "search", "print"]


def test_todos_los_iconos_de_la_barra_existen(qapp: object) -> None:
    ventana = MainWindow()

    for _accion, nombre in ventana._acciones_icono:
        assert (_DIR_ICONOS / f"{nombre}.svg").is_file(), nombre


def test_el_icono_de_guardar_es_un_disquete_no_una_descarga(qapp: object) -> None:
    """El de descarga (bandeja + flecha abajo) se coló una vez: guardar y
    descargar no son lo mismo y el usuario lo lee al vuelo por la forma."""
    svg = (_DIR_ICONOS / "save.svg").read_text(encoding="utf-8")

    # El disquete del diseño: carcasa con la esquina cortada, obturador y etiqueta.
    assert "M4.5 4h11.5L20 7.9V19" in svg
    # La flecha hacia abajo del icono de descarga que hubo antes.
    assert "M8 10.5 12 14.5l4-4" not in svg


def test_los_iconos_se_recolorean_con_el_tema(qapp: object) -> None:
    """Se cargan con `currentColor` sustituido: si algún SVG trajera el color
    fijo del diseño, el icono no seguiría al tema."""
    for ruta in _DIR_ICONOS.glob("*.svg"):
        assert "currentColor" in ruta.read_text(encoding="utf-8"), ruta.name


def test_los_iconos_del_repo_estan_en_el_paquete(qapp: object) -> None:
    """Los .svg viven en assets/icons y de ahí los lee el ejecutable."""
    assert _DIR_ICONOS.is_dir()
    assert len(list(_DIR_ICONOS.glob("*.svg"))) >= 19
    assert isinstance(base_recursos(), Path)
