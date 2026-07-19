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


def generar_todos(directorio: Path = DIRECTORIO_FIXTURES) -> dict[str, Path]:
    directorio.mkdir(parents=True, exist_ok=True)
    return {"simple": generar_pdf_simple(directorio / "simple.pdf")}


if __name__ == "__main__":
    rutas = generar_todos()
    for nombre, ruta in rutas.items():
        print(f"{nombre}: {ruta}")
