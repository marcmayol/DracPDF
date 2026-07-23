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


def generar_pdf_titulos_tabla(destino: Path) -> Path:
    """PDF de 2 páginas con títulos (fuente grande), texto de cuerpo y una tabla
    con bordes (3 filas × 2 columnas). Base de las conversiones salientes."""
    doc = fitz.open()
    p1 = doc.new_page(width=595.0, height=842.0)
    p1.insert_text((72, 80), "Informe de prueba", fontsize=24)  # título
    p1.insert_text((72, 120), "Resumen ejecutivo del documento.", fontsize=11)
    p1.insert_text((72, 150), "Contiene una tabla y varias secciones.", fontsize=11)

    # Tabla con bordes: 3 filas x 2 columnas.
    filas = [("Concepto", "Valor"), ("Ingresos", "1000"), ("Gastos", "400")]
    x0, y0, ancho_col, alto_fila = 72.0, 200.0, 180.0, 26.0
    for i, (a, b) in enumerate(filas):
        y = y0 + i * alto_fila
        p1.draw_rect(fitz.Rect(x0, y, x0 + ancho_col, y + alto_fila))
        p1.draw_rect(fitz.Rect(x0 + ancho_col, y, x0 + 2 * ancho_col, y + alto_fila))
        p1.insert_text((x0 + 6, y + 17), a, fontsize=11)
        p1.insert_text((x0 + ancho_col + 6, y + 17), b, fontsize=11)

    p2 = doc.new_page(width=595.0, height=842.0)
    p2.insert_text((72, 80), "Sección segunda", fontsize=20)  # título
    p2.insert_text((72, 120), "Contenido de la segunda página.", fontsize=11)

    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    doc.close()
    return destino


def generar_pdf_escaneado(destino: Path) -> Path:
    """PDF de una página SIN capa de texto (solo una imagen): simula un escaneo."""
    doc = fitz.open()
    pagina = doc.new_page(width=300.0, height=400.0)
    # Un pixmap rojo insertado como imagen; la página no tiene texto extraíble.
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 300, 400), False)
    pix.set_rect(pix.irect, (200, 60, 60))
    pagina.insert_image(pagina.rect, pixmap=pix)
    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    doc.close()
    return destino


def generar_pdf_parrafos(destino: Path) -> Path:
    """PDF con párrafos y tamaños de letra variados (Fase 9: corrección).

    Incluye el tramo "CINCUENTA" (tamaño 13) para corregir y una línea corta
    "OK" (tamaño 22) donde un texto largo no cabe: prueba el caso "no cabe".
    """
    doc = fitz.open()
    p = doc.new_page(width=420.0, height=300.0)
    p.insert_text((40, 70), "El pago acordado es de CINCUENTA euros.", fontsize=13)
    p.insert_text((40, 120), "Cláusula segunda del contrato firmado.", fontsize=11)
    p.insert_text((40, 180), "OK", fontsize=22)
    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    doc.close()
    return destino


def generar_pdf_con_imagenes(destino: Path) -> Path:
    """PDF de 2 páginas que comparten un logo (misma imagen), para el borrado de
    imágenes y el aviso de "imagen en varias páginas" (Fase 9, Parte C)."""
    logo = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 32, 32), False)
    logo.set_rect(logo.irect, (40, 90, 200))
    png = logo.tobytes("png")
    doc = fitz.open()
    for i in range(2):
        p = doc.new_page(width=300.0, height=300.0)
        p.insert_text((30, 40), f"Página {i + 1} con logo compartido.", fontsize=11)
        p.insert_image(fitz.Rect(60, 80, 160, 180), stream=png)
    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    doc.close()
    return destino


def generar_todos(directorio: Path = DIRECTORIO_FIXTURES) -> dict[str, Path]:
    directorio.mkdir(parents=True, exist_ok=True)
    return {
        "simple": generar_pdf_simple(directorio / "simple.pdf"),
        "contenido": generar_pdf_contenido(directorio / "contenido.pdf"),
        "titulos_tabla": generar_pdf_titulos_tabla(directorio / "titulos_tabla.pdf"),
        "escaneado": generar_pdf_escaneado(directorio / "escaneado.pdf"),
        "parrafos": generar_pdf_parrafos(directorio / "parrafos.pdf"),
        "con_imagenes": generar_pdf_con_imagenes(directorio / "con_imagenes.pdf"),
    }


if __name__ == "__main__":
    rutas = generar_todos()
    for nombre, ruta in rutas.items():
        print(f"{nombre}: {ruta}")
