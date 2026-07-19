"""Ventana principal. Actúa como raíz de composición: cablea el adaptador
PyMuPDF con los casos de uso y se los pasa a los widgets de la UI.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMainWindow

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.abrir_documento import AbrirDocumento
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_TITULO_BASE = "lectorpdf"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._repositorio = PyMuPDFDocumentRepository()
        self._abrir = AbrirDocumento(self._repositorio)
        self._renderizar = RenderizarPagina(self._repositorio)

        self._visor = ViewerWidget(self._renderizar)
        self.setCentralWidget(self._visor)
        self.setWindowTitle(_TITULO_BASE)
        self.resize(900, 1000)

    def abrir_ruta(self, ruta: Path) -> Documento:
        documento = self._abrir.ejecutar(ruta)
        self._visor.set_documento(documento)
        nombre = documento.titulo or ruta.name
        self.setWindowTitle(f"{nombre} — {_TITULO_BASE}")
        return documento
