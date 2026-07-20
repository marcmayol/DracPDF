"""Genera los PDF de fixture con formularios AcroForm para los tests.

Uso a mano:
    uv run python tests/adapters/generar_fixtures_formularios.py
"""

from __future__ import annotations

from pathlib import Path

import fitz

DIRECTORIO_FIXTURES = Path(__file__).parent / "fixtures"


def generar_formulario_completo(destino: Path) -> Path:
    """PDF con un campo de cada tipo: texto, casilla, radio (2), combo, lista,
    más un campo de texto de solo lectura."""
    doc = fitz.open()
    page = doc.new_page(width=400, height=600)

    _texto(page, "nombre", (50, 50, 300, 70), valor="")
    _casilla(page, "acepta", (50, 90, 70, 110))
    _combo(page, "pais", (50, 130, 300, 150), ["ES", "FR", "IT"])
    _lista(page, "color", (50, 170, 300, 230), ["rojo", "verde", "azul"])
    _radios(page, "genero", [(50, 250), (150, 250)])
    _texto(page, "referencia", (50, 300, 300, 320), valor="R-001", solo_lectura=True)

    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    doc.close()
    return destino


def generar_formulario_dos_textos(destino: Path) -> Path:
    """PDF con dos campos de texto con valor inicial ('a'='X', 'b'='Y').

    Se usa para deshacer/rehacer: PyMuPDF no persiste el valor vacío en un campo
    de texto, así que se parte de valores no vacíos para probar el orden."""
    doc = fitz.open()
    page = doc.new_page(width=400, height=300)
    _texto(page, "a", (50, 50, 300, 70), valor="X")
    _texto(page, "b", (50, 90, 300, 110), valor="Y")
    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    doc.close()
    return destino


def generar_xfa(destino: Path) -> Path:
    """PDF con una entrada /XFA en el AcroForm (sucedáneo detectable)."""
    doc = fitz.open()
    doc.new_page()
    catalogo = doc.pdf_catalog()
    doc.xref_set_key(catalogo, "AcroForm", "<<>>")
    doc.xref_set_key(catalogo, "AcroForm/XFA", "(formulario-xfa-de-prueba)")
    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    doc.close()
    return destino


# -- Constructores de widgets ----------------------------------------------


def _texto(
    page: fitz.Page,
    nombre: str,
    rect: tuple[float, float, float, float],
    valor: str,
    solo_lectura: bool = False,
) -> None:
    w = fitz.Widget()
    w.field_name = nombre
    w.field_type = fitz.PDF_WIDGET_TYPE_TEXT
    w.rect = fitz.Rect(*rect)
    w.field_value = valor
    if solo_lectura:
        w.field_flags = fitz.PDF_FIELD_IS_READ_ONLY
    page.add_widget(w)


def _casilla(
    page: fitz.Page, nombre: str, rect: tuple[float, float, float, float]
) -> None:
    w = fitz.Widget()
    w.field_name = nombre
    w.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
    w.rect = fitz.Rect(*rect)
    page.add_widget(w)


def _combo(
    page: fitz.Page,
    nombre: str,
    rect: tuple[float, float, float, float],
    opciones: list[str],
) -> None:
    w = fitz.Widget()
    w.field_name = nombre
    w.field_type = fitz.PDF_WIDGET_TYPE_COMBOBOX
    w.rect = fitz.Rect(*rect)
    w.choice_values = opciones
    page.add_widget(w)


def _lista(
    page: fitz.Page,
    nombre: str,
    rect: tuple[float, float, float, float],
    opciones: list[str],
) -> None:
    w = fitz.Widget()
    w.field_name = nombre
    w.field_type = fitz.PDF_WIDGET_TYPE_LISTBOX
    w.rect = fitz.Rect(*rect)
    w.choice_values = opciones
    page.add_widget(w)


def _radios(
    page: fitz.Page, nombre: str, posiciones: list[tuple[float, float]]
) -> None:
    for x, y in posiciones:
        w = fitz.Widget()
        w.field_name = nombre
        w.field_type = fitz.PDF_WIDGET_TYPE_RADIOBUTTON
        w.rect = fitz.Rect(x, y, x + 18, y + 18)
        w.field_value = False  # imprescindible para crearlo (queda "Off")
        page.add_widget(w)


def generar_todos(directorio: Path = DIRECTORIO_FIXTURES) -> dict[str, Path]:
    directorio.mkdir(parents=True, exist_ok=True)
    return {
        "formulario": generar_formulario_completo(directorio / "formulario.pdf"),
        "xfa": generar_xfa(directorio / "xfa.pdf"),
    }


if __name__ == "__main__":
    for nombre, ruta in generar_todos().items():
        print(f"{nombre}: {ruta}")
