"""Comprobación del criterio de aceptación de la Fase 1.

Genera un PDF grande (600 páginas con texto), lo abre en la ventana real y mide:

- el tiempo de render inicial (debe ser holgadamente < 2 s),
- cuántas páginas/miniaturas se renderizan al abrir (debe ser un puñado, no 600,
  lo que demuestra que abrir no bloquea recorriendo todo el documento),
- el tiempo de un salto de navegación y de un zoom (fluidez).

Uso:
    QT_QPA_PLATFORM=offscreen uv run python scripts/benchmark_visor.py
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import fitz
from PySide6.QtWidgets import QApplication

from lectorpdf.ui.main_window import MainWindow

NUM_PAGINAS = 600
LIMITE_SEGUNDOS = 2.0


def generar_pdf_grande(destino: Path, paginas: int) -> Path:
    doc = fitz.open()
    for i in range(paginas):
        pagina = doc.new_page(width=595.0, height=842.0)
        pagina.insert_text((72, 72), f"Página {i + 1} de {paginas}", fontsize=18)
        pagina.insert_text((72, 120), "Contenido de prueba " * 6, fontsize=11)
    doc.save(destino)
    doc.close()
    return destino


def main() -> int:
    app = QApplication([])

    ruta = Path(tempfile.gettempdir()) / "benchmark_600.pdf"
    t_gen = time.perf_counter()
    generar_pdf_grande(ruta, NUM_PAGINAS)
    print(f"PDF generado: {NUM_PAGINAS} páginas en {time.perf_counter() - t_gen:.2f} s")

    ventana = MainWindow()
    ventana.resize(1100, 900)
    ventana.show()

    t0 = time.perf_counter()
    documento = ventana.abrir_ruta(ruta)
    app.processEvents()  # fuerza el primer pintado
    t_abrir = time.perf_counter() - t0

    paginas_render = len(ventana._visor.indices_mostrados())
    miniaturas_render = len(ventana._miniaturas.miniaturas_renderizadas())

    t0 = time.perf_counter()
    ventana._visor.ir_a_pagina(450)
    app.processEvents()
    t_nav = time.perf_counter() - t0

    t0 = time.perf_counter()
    ventana._visor.zoom_acercar()
    app.processEvents()
    t_zoom = time.perf_counter() - t0

    print("-" * 56)
    print(f"Páginas totales:            {documento.num_paginas}")
    print(f"Render inicial:             {t_abrir:.3f} s  (límite {LIMITE_SEGUNDOS} s)")
    print(f"Páginas renderizadas:       {paginas_render}  (no {NUM_PAGINAS})")
    print(f"Miniaturas renderizadas:    {miniaturas_render}  (no {NUM_PAGINAS})")
    print(f"Salto a la página 450:      {t_nav:.3f} s")
    print(f"Zoom (acercar):             {t_zoom:.3f} s")
    print("-" * 56)

    ok = (
        t_abrir < LIMITE_SEGUNDOS
        and paginas_render < NUM_PAGINAS
        and miniaturas_render < NUM_PAGINAS
    )
    print("RESULTADO:", "OK" if ok else "FALLO")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
