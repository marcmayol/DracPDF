"""Ventana principal. Actúa como raíz de composición: cablea el adaptador
PyMuPDF con los casos de uso y conecta el visor con el panel de miniaturas y la
barra de herramientas.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.core.domain.errores import ErrorDominio
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.abrir_documento import AbrirDocumento
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.thumbnails.thumbnail_panel import ThumbnailPanel
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_TITULO_BASE = "lectorpdf"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._repositorio = PyMuPDFDocumentRepository()
        self._abrir = AbrirDocumento(self._repositorio)
        self._renderizar = RenderizarPagina(self._repositorio)

        self._visor = ViewerWidget(self._renderizar)
        self._miniaturas = ThumbnailPanel(self._renderizar)
        self.setCentralWidget(self._visor)

        self._construir_dock_miniaturas()
        self._etiqueta_pagina = QLabel("—")
        self._construir_barra()
        self._conectar_senales()

        self.setAcceptDrops(True)
        self.setWindowTitle(_TITULO_BASE)
        self.resize(1100, 1000)

    # -- Construcción de la UI ----------------------------------------------

    def _construir_dock_miniaturas(self) -> None:
        dock = QDockWidget("Miniaturas", self)
        dock.setWidget(self._miniaturas)
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def _construir_barra(self) -> None:
        barra = QToolBar("Navegación", self)
        self.addToolBar(barra)

        self._accion(barra, "Abrir…", self._abrir_por_dialogo)
        barra.addSeparator()
        self._accion(barra, "◀ Anterior", self._visor.pagina_anterior)
        self._accion(barra, "Siguiente ▶", self._visor.pagina_siguiente)
        barra.addSeparator()
        self._accion(barra, "− Alejar", self._visor.zoom_alejar)
        self._accion(barra, "+ Acercar", self._visor.zoom_acercar)
        self._accion(barra, "Ajustar ancho", self._visor.ajustar_a_ancho)
        self._accion(barra, "Ajustar página", self._visor.ajustar_a_pagina)
        barra.addSeparator()
        barra.addWidget(self._etiqueta_pagina)

    def _accion(self, barra: QToolBar, texto: str, callback: Callable[[], None]) -> None:
        accion = QAction(texto, self)
        accion.triggered.connect(callback)
        barra.addAction(accion)

    def _conectar_senales(self) -> None:
        self._visor.pagina_cambiada.connect(self._miniaturas.seleccionar_pagina)
        self._visor.pagina_cambiada.connect(self._actualizar_etiqueta)
        self._miniaturas.pagina_seleccionada.connect(self._visor.ir_a_pagina)

    # -- Acciones -----------------------------------------------------------

    def abrir_ruta(self, ruta: Path) -> Documento:
        documento = self._abrir.ejecutar(ruta)
        self._visor.set_documento(documento)
        self._miniaturas.set_documento(documento)
        nombre = documento.titulo or ruta.name
        self.setWindowTitle(f"{nombre} — {_TITULO_BASE}")
        self._actualizar_etiqueta(0)
        return documento

    def abrir_ruta_con_aviso(self, ruta: Path) -> bool:
        """Abre `ruta` mostrando un aviso si falla, en vez de propagar el error."""
        try:
            self.abrir_ruta(ruta)
            return True
        except ErrorDominio as exc:
            QMessageBox.warning(self, "No se pudo abrir el documento", str(exc))
            return False

    def _abrir_por_dialogo(self) -> None:
        ruta_str, _ = QFileDialog.getOpenFileName(
            self, "Abrir PDF", "", "Documentos PDF (*.pdf)"
        )
        if ruta_str:
            self.abrir_ruta_con_aviso(Path(ruta_str))

    def _actualizar_etiqueta(self, indice: int) -> None:
        documento = self._visor.documento
        total = documento.num_paginas if documento is not None else 0
        self._etiqueta_pagina.setText(f"Página {indice + 1} / {total}")

    # -- Arrastrar y soltar -------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime = event.mimeData()
        if mime is not None and _ruta_pdf_de(mime) is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        ruta = _ruta_pdf_de(mime) if mime is not None else None
        if ruta is not None:
            event.acceptProposedAction()
            self.abrir_ruta_con_aviso(ruta)
        else:
            event.ignore()


def _ruta_pdf_de(mime: QMimeData) -> Path | None:
    """Primera ruta local con extensión .pdf entre las URLs arrastradas."""
    if not mime.hasUrls():
        return None
    for url in mime.urls():
        if url.isLocalFile():
            ruta = Path(url.toLocalFile())
            if ruta.suffix.lower() == ".pdf":
                return ruta
    return None
