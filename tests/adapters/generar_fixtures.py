"""Genera los PDF de fixture usados por los tests de integración.

Se ejecuta desde los tests (conftest) o a mano:

    uv run python tests/adapters/generar_fixtures.py
"""

from __future__ import annotations

from pathlib import Path

import fitz

DIRECTORIO_FIXTURES = Path(__file__).parent / "fixtures"

# Páginas con tamaños distintos para verificar que se leen las dimensiones reales.
_TAMANOS_PT: tuple[tuple[float, float], ...] = (
    (595.0, 842.0),  # A4 vertical
    (842.0, 595.0),  # A4 apaisado
    (612.0, 792.0),  # Carta
)


def generar_pdf_simple(destino: Path) -> Path:
    """PDF de 3 páginas con tamaños distintos y algo de texto."""
    doc = fitz.open()
    for i, (ancho, alto) in enumerate(_TAMANOS_PT):
        pagina = doc.new_page(width=ancho, height=alto)
        pagina.insert_text((72, 72), f"Página {i + 1}", fontsize=24)
    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    doc.close()
    return destino


def generar_pdf_contenido(destino: Path) -> Path:
    """PDF de 3 páginas con índice (outline), enlaces (interno + externo), texto
    buscable y metadatos. Base de los tests de la Fase 8 (visor).

    El término "Ladon" aparece 3 veces (2 en la página 1, 1 en la 2). La página 1
    contiene la frase exacta "frase exacta seleccionable" para el test de copia.
    """
    doc = fitz.open()
    p1 = doc.new_page(width=595.0, height=842.0)
    p1.insert_text((72, 72), "Ladon custodia el jardin. Ladon vigila.", fontsize=18)
    p1.insert_text((72, 120), "frase exacta seleccionable", fontsize=18)
    p2 = doc.new_page(width=595.0, height=842.0)
    p2.insert_text((72, 72), "Segunda pagina: Ladon aparece aqui.", fontsize=18)
    doc.new_page(width=595.0, height=842.0).insert_text(
        (72, 72), "Tercera y ultima pagina.", fontsize=18
    )
    doc.set_toc(
        [[1, "Portada", 1], [2, "Introduccion", 1], [1, "Desarrollo", 2], [1, "Cierre", 3]]
    )
    doc.set_metadata({"title": "Documento Ladon", "author": "Marc Mayol"})
    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    doc.close()
    # Segunda pasada: los enlaces se insertan sobre una página PDF ya persistida.
    doc = fitz.open(destino)
    doc[0].insert_link(
        {"kind": fitz.LINK_GOTO, "from": fitz.Rect(72, 160, 300, 180), "page": 1}
    )
    doc[0].insert_link(
        {
            "kind": fitz.LINK_URI,
            "from": fitz.Rect(72, 200, 300, 220),
            "uri": "https://example.com/",
        }
    )
    doc.save(str(destino), incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()
    return destino


def generar_todos(directorio: Path = DIRECTORIO_FIXTURES) -> dict[str, Path]:
    directorio.mkdir(parents=True, exist_ok=True)
    return {
        "simple": generar_pdf_simple(directorio / "simple.pdf"),
        "contenido": generar_pdf_contenido(directorio / "contenido.pdf"),
    }


if __name__ == "__main__":
    rutas = generar_todos()
    for nombre, ruta in rutas.items():
        print(f"{nombre}: {ruta}")
