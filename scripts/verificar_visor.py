"""Criterio de aceptación de la Fase 8 (fundamentos de visor).

Ejercita la pila real sobre un PDF de fixture (con índice, enlaces y texto) y
comprueba, uno a uno, los puntos del criterio de aceptación:

  1. la búsqueda encuentra las ocurrencias correctas y navega,
  2. seleccionar un rango conocido copia exactamente ese texto,
  3. el índice del panel coincide con get_toc(),
  4. imprimir a un QPrinter PDF virtual produce el número de páginas del rango,
  5. recientes, última página y zoom persisten al cerrar y reabrir,
  6. una segunda invocación llega a la instancia existente,
  7. deshacer tras editar dos campos restaura los valores en orden.

Uso:
    QT_QPA_PLATFORM=offscreen uv run python scripts/verificar_visor.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz  # noqa: E402
from PySide6.QtNetwork import QLocalSocket  # noqa: E402
from PySide6.QtPrintSupport import QPrinter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.adapters.generar_fixtures import generar_pdf_contenido  # noqa: E402
from tests.adapters.generar_fixtures_formularios import (  # noqa: E402
    generar_formulario_dos_textos,
)

from lectorpdf.ui import main_window as mw  # noqa: E402
from lectorpdf.ui.impresion.impresion import imprimir_documento  # noqa: E402
from lectorpdf.ui.instancia_unica import InstanciaUnica  # noqa: E402
from lectorpdf.ui.main_window import MainWindow  # noqa: E402

_resultados: list[tuple[str, bool]] = []


def _check(nombre: str, condicion: bool) -> None:
    _resultados.append((nombre, condicion))


def _limpiar(ventana: MainWindow) -> None:
    for clave in ("estado", mw._CLAVE_RECIENTES, "sesion"):
        ventana._prefs.remove(clave)


def main() -> int:
    QApplication.instance() or QApplication([])
    tmp = Path(tempfile.mkdtemp())
    contenido = generar_pdf_contenido(tmp / "contenido.pdf")

    ventana = MainWindow()
    doc = ventana.abrir_ruta(contenido)

    # 1. Búsqueda.
    ventana._ejecutar_busqueda("Ladon", False)
    _check("Búsqueda: 3 ocurrencias", len(ventana._coincidencias) == 3)
    ventana._busqueda_siguiente()
    _check("Búsqueda: navega (índice 1)", ventana._indice_coincidencia == 1)
    ventana._cerrar_busqueda()

    # 2. Selección y copia de un rango conocido.
    palabras = ventana._obtener_palabras.ejecutar(doc, 0)
    textos = [p.texto for p in palabras]
    i = textos.index("frase")
    ini, fin = palabras[i].rect_pt, palabras[i + 2].rect_pt
    capa = ventana._capa_seleccion
    capa._iniciar_arrastre(0, (ini.x0 + ini.x1) / 2, (ini.y0 + ini.y1) / 2)
    capa._extender_arrastre((fin.x0 + fin.x1) / 2, (fin.y0 + fin.y1) / 2)
    copiado = capa.copiar()
    _check("Selección copia el texto exacto", copiado == "frase exacta seleccionable")

    # 3. Índice = get_toc().
    entradas = ventana._obtener_indice.ejecutar(doc)
    origen = fitz.open(contenido)
    toc = origen.get_toc()
    origen.close()
    coincide = len(entradas) == len(toc) and all(
        e.titulo == t[1] and e.pagina == t[2] - 1
        for e, t in zip(entradas, toc, strict=False)
    )
    _check("Índice coincide con get_toc()", coincide)

    # 4. Impresión a PDF virtual del rango 2..3 (2 páginas).
    salida = tmp / "impreso.pdf"
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(salida))
    printer.setResolution(150)
    imprimir_documento(printer, doc, ventana._renderizar, 1, 2)
    impreso = fitz.open(salida)
    _check("Impresión del rango: 2 páginas", impreso.page_count == 2)
    impreso.close()

    # 5. Recientes, última página y zoom persisten al cerrar/reabrir.
    ventana._visor.ir_a_pagina(2)
    ventana._visor.set_escala(1.75)
    ventana._guardar_estado_documento(doc, ventana._vista())
    _check("Recientes registra el documento", str(contenido) in ventana._recientes())
    otra = MainWindow()
    otra.abrir_ruta(contenido)
    _check("Reabrir restaura la página", otra._visor.pagina_actual() == 2)
    _check("Reabrir restaura el zoom", otra._visor.escala == 1.75)
    _limpiar(otra)

    # 6. Segunda invocación llega a la instancia existente.
    servidor = InstanciaUnica("dracpdf-acept-fase8")
    servidor.iniciar_servidor()
    cliente = QLocalSocket()
    cliente.connectToServer("dracpdf-acept-fase8")
    _check("Instancia única: el cliente conecta", cliente.waitForConnected(300))
    cliente.abort()

    # 7. Deshacer tras editar dos campos.
    form = generar_formulario_dos_textos(tmp / "dos.pdf")
    doc2 = ventana.abrir_ruta(form)
    campos = ventana._listar.ejecutar(doc2)
    a = next(c for c in campos if c.nombre == "a")
    b = next(c for c in campos if c.nombre == "b")
    ventana._rellenar.ejecutar(doc2, a, "Marc")
    ventana._rellenar.ejecutar(doc2, b, "Mayol")
    ventana._deshacer()
    valor_b = next(c.valor for c in ventana._listar.ejecutar(doc2) if c.id == b.id)
    ventana._deshacer()
    valor_a = next(c.valor for c in ventana._listar.ejecutar(doc2) if c.id == a.id)
    _check("Deshacer restaura en orden", valor_b == "Y" and valor_a == "X")

    _limpiar(ventana)

    print("-" * 56)
    ok = True
    for nombre, cond in _resultados:
        print(f"  [{'OK' if cond else 'FALLO'}] {nombre}")
        ok = ok and cond
    print("-" * 56)
    print("RESULTADO:", "OK" if ok else "FALLO")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
