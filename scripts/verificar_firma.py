"""Criterio de aceptación de la Fase 3.

Dibuja una firma en el canvas, la exporta a PNG transparente, la estampa sobre un
PDF con texto (a través de la pila real: EstamparFirma + adaptador PyMuPDF),
guarda de forma incremental, reabre y verifica con PyMuPDF que la imagen
insertada conserva el canal alfa (SMask). Deja además el PDF firmado y un preview
PNG para la comprobación visual en Adobe/otro visor.

Uso:
    uv run python scripts/verificar_firma.py
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz  # noqa: E402
from PySide6.QtCore import QEvent, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from lectorpdf.adapters.pymupdf.document_repository import (  # noqa: E402
    PyMuPDFDocumentRepository,
)
from lectorpdf.adapters.pymupdf.estampado_service import (  # noqa: E402
    PyMuPDFEstampadoService,
)
from lectorpdf.adapters.pymupdf.form_service import PyMuPDFFormService  # noqa: E402
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos  # noqa: E402
from lectorpdf.core.domain.formularios import RectanguloPt  # noqa: E402
from lectorpdf.core.use_cases.estampar_firma import EstamparFirma  # noqa: E402
from lectorpdf.core.use_cases.guardar_formulario import GuardarFormulario  # noqa: E402
from lectorpdf.ui.signature.signature_canvas import SignatureCanvas  # noqa: E402


def _dibujar_firma() -> bytes:
    """Simula una firma manuscrita y la exporta a PNG transparente."""
    canvas = SignatureCanvas()
    trazos = [
        [(20, 80), (40, 20), (60, 80), (80, 30), (100, 80)],  # zig-zag tipo "M"
        [(110, 40), (150, 45), (190, 35)],  # rúbrica
    ]
    for trazo in trazos:
        x0, y0 = trazo[0]
        canvas.mousePressEvent(
            QMouseEvent(
                QEvent.Type.MouseButtonPress,
                QPointF(x0, y0),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
        )
        for x, y in trazo[1:]:
            canvas.mouseMoveEvent(
                QMouseEvent(
                    QEvent.Type.MouseMove,
                    QPointF(x, y),
                    Qt.MouseButton.NoButton,
                    Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier,
                )
            )
    return canvas.exportar_png()


def _pdf_con_texto(destino: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=420, height=300)
    page.insert_text((40, 60), "CONTRATO DE PRUEBA", fontsize=18)
    page.insert_text((40, 100), "El abajo firmante acepta las condiciones.", fontsize=11)
    page.insert_text((40, 240), "Firma:", fontsize=12)
    doc.save(destino)
    doc.close()


def main() -> int:
    QApplication.instance() or QApplication([])

    tmp = Path(tempfile.gettempdir())
    pdf = tmp / "lectorpdf_firma_demo.pdf"
    preview = tmp / "lectorpdf_firma_demo_preview.png"

    _pdf_con_texto(pdf)
    png_firma = _dibujar_firma()

    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(pdf)
    EstamparFirma(PyMuPDFEstampadoService(registro)).ejecutar(
        documento, 0, RectanguloPt(90, 225, 250, 285), png_firma
    )
    GuardarFormulario(PyMuPDFFormService(registro)).ejecutar(documento)  # incremental
    registro.cerrar(documento.id)

    # Reabrir con PyMuPDF puro y verificar el alfa (SMask) de la imagen insertada.
    reabierto = fitz.open(pdf)
    imagenes = reabierto[0].get_images(full=True)
    tiene_imagen = len(imagenes) == 1
    smask = imagenes[0][1] if tiene_imagen else 0
    reabierto[0].get_pixmap(matrix=fitz.Matrix(2, 2)).save(preview)  # preview visual
    reabierto.close()

    conserva_alfa = tiene_imagen and smask != 0

    smask_txt = f"sí (xref {smask})" if smask else "NO"
    print("-" * 60)
    print(f"Imagen insertada en la página:  {'sí' if tiene_imagen else 'NO'}")
    print(f"SMask (canal alfa) presente:    {smask_txt}")
    print(f"PDF firmado:                    {pdf}")
    print(f"Preview para revisión visual:   {preview}")
    print("-" * 60)
    print("RESULTADO:", "OK" if conserva_alfa else "FALLO")
    print(
        "Comprobación visual: abre el PDF firmado en Adobe Reader y verifica que "
        "la firma se ve sobre 'Firma:' con el fondo transparente (se lee el texto "
        "de la página a través de los huecos del trazo)."
    )
    return 0 if conserva_alfa else 1


if __name__ == "__main__":
    raise SystemExit(main())
