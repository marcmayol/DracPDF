"""Ventana principal. Actúa como raíz de composición: cablea el adaptador
PyMuPDF con los casos de uso y conecta el visor con el panel de miniaturas y la
barra de herramientas.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from lectorpdf.adapters.pyhanko.signature_service import PyHankoSignatureService
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.estampado_service import PyMuPDFEstampadoService
from lectorpdf.adapters.pymupdf.form_service import PyMuPDFFormService
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.errores import ErrorDominio, FormularioXFANoSoportado
from lectorpdf.core.domain.firma_digital import ConfigFirma
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.abrir_documento import AbrirDocumento
from lectorpdf.core.use_cases.estampar_firma import EstamparFirma
from lectorpdf.core.use_cases.firmar_digitalmente import FirmarDigitalmente
from lectorpdf.core.use_cases.guardar_formulario import GuardarFormulario
from lectorpdf.core.use_cases.listar_campos import ListarCampos
from lectorpdf.core.use_cases.rellenar_campo import RellenarCampo
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.core.use_cases.verificar_firmas import VerificarFirmas
from lectorpdf.ui.forms.form_layer import FormLayer
from lectorpdf.ui.signature.biblioteca_firmas import (
    BibliotecaFirmas,
    directorio_por_defecto,
)
from lectorpdf.ui.signature.digital_seal_layer import DigitalSealLayer
from lectorpdf.ui.signature.digital_signature_dialog import DigitalSignatureDialog
from lectorpdf.ui.signature.signature_dialog import SignatureDialog
from lectorpdf.ui.signature.signature_layer import SignatureLayer
from lectorpdf.ui.signature.verification_panel import VerificationPanel
from lectorpdf.ui.theme.estilos import (
    aplicar_tema,
    cargar_tema_preferido,
    guardar_preferencia_tema,
)
from lectorpdf.ui.theme.iconos import icono
from lectorpdf.ui.theme.tokens import TEMA_CLARO, TEMA_OSCURO
from lectorpdf.ui.thumbnails.thumbnail_panel import ThumbnailPanel
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_TITULO_BASE = "lectorpdf"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        # Raíz de composición: un registro compartido para todos los adaptadores.
        self._registro = RegistroDocumentos()
        self._repositorio = PyMuPDFDocumentRepository(self._registro)
        self._servicio_form = PyMuPDFFormService(self._registro)
        self._servicio_estampado = PyMuPDFEstampadoService(self._registro)
        self._servicio_firma = PyHankoSignatureService(self._registro)

        self._abrir = AbrirDocumento(self._repositorio)
        self._renderizar = RenderizarPagina(self._repositorio)
        self._listar = ListarCampos(self._servicio_form)
        self._rellenar = RellenarCampo(self._servicio_form)
        self._guardar_form = GuardarFormulario(self._servicio_form)
        self._estampar = EstamparFirma(self._servicio_estampado)
        self._firmar_digital = FirmarDigitalmente(self._servicio_firma)
        self._verificar = VerificarFirmas(self._servicio_firma)

        self._documento: Documento | None = None
        self._tema = cargar_tema_preferido()
        self._acciones_icono: list[tuple[QAction, str]] = []

        self._visor = ViewerWidget(self._renderizar)
        self._miniaturas = ThumbnailPanel(self._renderizar)
        self._capa_form = FormLayer(self._visor, self._rellenar)
        self._capa_firma = SignatureLayer(self._visor, self._estampar)
        self._capa_sello = DigitalSealLayer(self._visor, self._firmar_digital)
        self._biblioteca = BibliotecaFirmas(directorio_por_defecto())
        self.setCentralWidget(self._visor)

        self._construir_dock_miniaturas()
        self._panel_verificacion = VerificationPanel()
        self._construir_dock_verificacion()
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

    def _construir_dock_verificacion(self) -> None:
        dock = QDockWidget("Firmas digitales", self)
        dock.setWidget(self._panel_verificacion)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _construir_barra(self) -> None:
        barra = QToolBar("Navegación", self)
        self.addToolBar(barra)

        self._accion_icono(barra, "open", "Abrir…", self._abrir_por_dialogo)
        self._accion_icono(barra, "save", "Guardar", self._guardar)
        barra.addSeparator()
        self._accion_icono(barra, "page-prev", "Página anterior", self._visor.pagina_anterior)
        self._accion_icono(barra, "page-next", "Página siguiente", self._visor.pagina_siguiente)
        barra.addSeparator()
        self._accion_icono(barra, "zoom-out", "Alejar", self._visor.zoom_alejar)
        self._accion_icono(barra, "zoom-in", "Acercar", self._visor.zoom_acercar)
        self._accion(barra, "Ajustar ancho", self._visor.ajustar_a_ancho)
        self._accion(barra, "Ajustar página", self._visor.ajustar_a_pagina)
        barra.addSeparator()
        self._accion_icono(barra, "sign-draw", "Dibujar y estampar firma", self._iniciar_firma)
        self._accion_icono(barra, "sign-cert", "Firmar con certificado", self._firmar_digitalmente)
        self._accion(barra, "✓ Colocar", self._confirmar_firma)
        self._accion(barra, "✗ Cancelar", self._cancelar_colocacion)
        barra.addSeparator()
        self._accion_icono(barra, "verify", "Verificar firmas", self._verificar_firmas)
        barra.addSeparator()
        self._accion(barra, "Cambiar tema", self._conmutar_tema)
        barra.addWidget(self._etiqueta_pagina)

    def _accion(self, barra: QToolBar, texto: str, callback: Callable[[], None]) -> None:
        accion = QAction(texto, self)
        accion.triggered.connect(callback)
        barra.addAction(accion)

    def _accion_icono(
        self,
        barra: QToolBar,
        nombre_icono: str,
        tooltip: str,
        callback: Callable[[], None],
    ) -> None:
        accion = QAction(icono(nombre_icono, self._tema.text), tooltip, self)
        accion.setToolTip(tooltip)
        accion.triggered.connect(callback)
        barra.addAction(accion)
        self._acciones_icono.append((accion, nombre_icono))

    def _conectar_senales(self) -> None:
        self._visor.pagina_cambiada.connect(self._miniaturas.seleccionar_pagina)
        self._visor.pagina_cambiada.connect(self._actualizar_etiqueta)
        self._miniaturas.pagina_seleccionada.connect(self._visor.ir_a_pagina)

    # -- Acciones -----------------------------------------------------------

    def abrir_ruta(self, ruta: Path) -> Documento:
        documento = self._abrir.ejecutar(ruta)
        self._documento = documento
        self._visor.set_documento(documento)
        self._miniaturas.set_documento(documento)
        self._cargar_formulario(documento)
        nombre = documento.titulo or ruta.name
        self.setWindowTitle(f"{nombre} — {_TITULO_BASE}")
        self._actualizar_etiqueta(0)
        return documento

    def _cargar_formulario(self, documento: Documento) -> None:
        """Lista los campos y los pasa al overlay; avisa si el PDF es XFA."""
        try:
            campos = self._listar.ejecutar(documento)
        except FormularioXFANoSoportado:
            self._capa_form.set_campos((), documento=documento)
            QMessageBox.warning(
                self,
                "Formulario no soportado",
                "Este PDF usa formularios XFA, no soportados. Se abre solo como "
                "visor; no se pueden rellenar sus campos.",
            )
            return
        self._capa_form.set_campos(campos, documento=documento)

    def _guardar(self) -> None:
        if self._documento is None:
            return
        try:
            self._guardar_form.ejecutar(self._documento)
        except Exception as exc:  # errores de E/S de PyMuPDF al guardar
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def _iniciar_firma(self) -> None:
        if self._documento is None:
            return
        dialogo = SignatureDialog(self, self._biblioteca)
        if dialogo.exec() != SignatureDialog.DialogCode.Accepted:
            return
        png = dialogo.png()
        if png:
            self._capa_firma.iniciar_colocacion(self._documento, png)

    def _confirmar_firma(self) -> None:
        if self._capa_sello.colocando():
            try:
                self._capa_sello.confirmar()
            except ErrorDominio as exc:
                QMessageBox.warning(self, "No se pudo firmar", str(exc))
                return
            self._tras_firmar()
            return
        try:
            self._capa_firma.confirmar()
        except ErrorDominio as exc:
            QMessageBox.warning(self, "No se pudo estampar la firma", str(exc))

    def _cancelar_colocacion(self) -> None:
        self._capa_firma.cancelar()
        self._capa_sello.cancelar()

    def _firmar_digitalmente(self) -> None:
        if self._documento is None:
            return
        if self._guardar_form.hay_cambios_sin_guardar(self._documento):
            QMessageBox.information(
                self,
                "Cambios sin guardar",
                "Se guardarán los cambios pendientes y luego se firmará el fichero.",
            )
        dialogo = DigitalSignatureDialog(self)
        if dialogo.exec() != DigitalSignatureDialog.DialogCode.Accepted:
            return
        credencial = dialogo.credencial()
        if credencial is None:
            return
        if dialogo.sello_visible():
            self._capa_sello.iniciar_colocacion(
                self._documento, credencial, dialogo.razon()
            )
            return
        # Firma invisible: en la página actual, sin sello.
        config = ConfigFirma(pagina=self._visor.pagina_actual(), razon=dialogo.razon())
        try:
            self._firmar_digital.ejecutar(self._documento, config, credencial)
        except ErrorDominio as exc:
            QMessageBox.warning(self, "No se pudo firmar", str(exc))
            return
        for indice in range(self._documento.num_paginas):
            self._visor.invalidar_pagina(indice)
        self._tras_firmar()

    def _tras_firmar(self) -> None:
        """El documento queda firmado: se bloquea la edición de formularios y se
        actualiza el panel de verificación."""
        if self._documento is None:
            return
        self._capa_form.set_campos((), documento=self._documento)
        resultados = self._verificar.ejecutar(self._documento, [])
        self._panel_verificacion.mostrar(resultados)

    def _verificar_firmas(self) -> None:
        if self._documento is None:
            return
        # Ancla de confianza opcional (certificado en DER/PEM/CER).
        ruta_ancla, _ = QFileDialog.getOpenFileName(
            self,
            "Certificado de confianza (opcional)",
            "",
            "Certificados (*.der *.pem *.cer *.crt)",
        )
        anclas = [Path(ruta_ancla)] if ruta_ancla else []
        resultados = self._verificar.ejecutar(self._documento, anclas)
        self._panel_verificacion.mostrar(resultados)

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

    def _conmutar_tema(self) -> None:
        nuevo = TEMA_CLARO if self._tema.es_oscuro else TEMA_OSCURO
        app = QApplication.instance()
        if isinstance(app, QApplication):
            aplicar_tema(app, nuevo)
        guardar_preferencia_tema(nuevo.nombre)
        self._tema = nuevo
        for accion, nombre_icono in self._acciones_icono:
            accion.setIcon(icono(nombre_icono, self._tema.text))

    def _actualizar_etiqueta(self, indice: int) -> None:
        documento = self._visor.documento
        total = documento.num_paginas if documento is not None else 0
        self._etiqueta_pagina.setText(f"Página {indice + 1} / {total}")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._documento is not None and self._guardar_form.hay_cambios_sin_guardar(
            self._documento
        ):
            respuesta = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Guardar antes de cerrar?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if respuesta == QMessageBox.StandardButton.Save:
                self._guardar()
                event.accept()
            elif respuesta == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

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
