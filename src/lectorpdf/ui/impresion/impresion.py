"""Pintado del documento sobre un QPrinter (impresión o exportación a PDF).

Renderiza cada página del rango a la resolución de la impresora (topada a un
máximo razonable para no generar mapas de bits enormes) y la dibuja centrada y a
escala en la página de la impresora, preservando la proporción. No modifica el
documento: es pura presentación.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrinter

from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.viewer.imagen import qimagen_desde

#: Tope de DPI del ráster: a 600 DPI un A4 son ~9500 px de ancho; 300 basta para
#: impresión y evita mapas de bits desmesurados.
_DPI_MAX = 300


def imprimir_documento(
    printer: QPrinter,
    documento: Documento,
    caso_render: RenderizarPagina,
    primera: int,
    ultima: int,
) -> int:
    """Pinta las páginas [primera, ultima] (0-based, inclusive) en `printer`.

    Devuelve el número de páginas pintadas."""
    primera = max(0, primera)
    ultima = min(ultima, documento.num_paginas - 1)
    if primera > ultima:
        return 0

    dpi = min(printer.resolution(), _DPI_MAX)
    escala = dpi / 72.0

    painter = QPainter(printer)
    try:
        pintadas = 0
        for indice in range(primera, ultima + 1):
            if pintadas > 0:
                printer.newPage()
            imagen = caso_render.ejecutar(documento, indice, escala)
            qimg = qimagen_desde(imagen)
            destino = _rect_ajustado(
                printer.pageRect(QPrinter.Unit.DevicePixel),
                qimg.width(),
                qimg.height(),
            )
            painter.drawImage(destino, qimg)
            pintadas += 1
        return pintadas
    finally:
        painter.end()


def _rect_ajustado(disponible: QRectF, ancho: int, alto: int) -> QRectF:
    """Rect que encaja una imagen ancho×alto dentro de `disponible`, centrado y
    conservando la proporción."""
    if ancho <= 0 or alto <= 0:
        return disponible
    escala = min(disponible.width() / ancho, disponible.height() / alto)
    w = ancho * escala
    h = alto * escala
    x = disponible.left() + (disponible.width() - w) / 2.0
    y = disponible.top() + (disponible.height() - h) / 2.0
    return QRectF(x, y, w, h)
