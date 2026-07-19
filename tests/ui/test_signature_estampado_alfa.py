"""Integración: canvas -> PNG -> estampar -> guardar -> reabrir, con alfa.

Ejercita la cadena completa de la Fase 3 y verifica que la imagen insertada
conserva el canal alfa (SMask) al reabrir con PyMuPDF.
"""

from __future__ import annotations

from pathlib import Path

import fitz
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.estampado_service import PyMuPDFEstampadoService
from lectorpdf.adapters.pymupdf.form_service import PyMuPDFFormService
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.ui.signature.signature_canvas import SignatureCanvas


def _firma_png(qapp_asegurado: bool = True) -> bytes:
    canvas = SignatureCanvas()
    canvas.mousePressEvent(
        QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(10, 50),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    for x, y in [(40, 15), (80, 55), (120, 20)]:
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


def test_estampado_conserva_alfa_al_reabrir(qapp: object, tmp_path: Path) -> None:
    ruta = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page(width=300, height=400)
    doc.save(ruta)
    doc.close()

    png = _firma_png()

    registro = RegistroDocumentos()
    documento = PyMuPDFDocumentRepository(registro).abrir(ruta)
    PyMuPDFEstampadoService(registro).estampar_imagen(
        documento.id, 0, RectanguloPt(50, 50, 250, 150), png
    )
    PyMuPDFFormService(registro).guardar_incremental(documento.id, None)
    registro.cerrar(documento.id)

    # Reabrir con PyMuPDF puro y comprobar el SMask de la imagen insertada.
    reabierto = fitz.open(ruta)
    imagenes = reabierto[0].get_images(full=True)
    assert len(imagenes) == 1
    smask_xref = imagenes[0][1]
    assert smask_xref != 0  # tiene canal alfa (máscara suave)
    reabierto.close()
