"""Ventana principal. Actúa como raíz de composición: cablea el adaptador
PyMuPDF con los casos de uso y conecta el visor con el panel de miniaturas y la
barra de herramientas.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QMimeData, QSettings, Qt, QUrl
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QDesktopServices,
    QDragEnterEvent,
    QDropEvent,
    QIcon,
    QKeySequence,
    QShortcut,
)
from PySide6.QtPrintSupport import (
    QAbstractPrintDialog,
    QPrintDialog,
    QPrinter,
    QPrintPreviewDialog,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from lectorpdf.adapters.pyhanko.signature_service import PyHankoSignatureService
from lectorpdf.adapters.pymupdf.contenido import PyMuPDFContenido
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.estampado_service import PyMuPDFEstampadoService
from lectorpdf.adapters.pymupdf.form_service import PyMuPDFFormService
from lectorpdf.adapters.pymupdf.herramientas import PyMuPDFHerramientas
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.contenido import Coincidencia
from lectorpdf.core.domain.errores import ErrorDominio, FormularioXFANoSoportado
from lectorpdf.core.domain.firma_digital import ConfigFirma
from lectorpdf.core.domain.herramientas import ResultadoCompresion
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.abrir_documento import AbrirDocumento
from lectorpdf.core.use_cases.buscar_en_documento import BuscarEnDocumento
from lectorpdf.core.use_cases.comprimir_pdf import ComprimirPdf
from lectorpdf.core.use_cases.desproteger_pdf import DesprotegerPdf
from lectorpdf.core.use_cases.dividir_pdf import DividirPdf
from lectorpdf.core.use_cases.estampar_firma import EstamparFirma
from lectorpdf.core.use_cases.exportar_imagenes import DPI_POR_DEFECTO, ExportarImagenes
from lectorpdf.core.use_cases.exportar_texto import ExportarTexto
from lectorpdf.core.use_cases.firmar_digitalmente import FirmarDigitalmente
from lectorpdf.core.use_cases.guardar_formulario import GuardarFormulario
from lectorpdf.core.use_cases.listar_campos import ListarCampos
from lectorpdf.core.use_cases.obtener_enlaces import ObtenerEnlaces
from lectorpdf.core.use_cases.obtener_indice import ObtenerIndice
from lectorpdf.core.use_cases.obtener_palabras import ObtenerPalabras
from lectorpdf.core.use_cases.organizar_paginas import OrganizarPaginas
from lectorpdf.core.use_cases.proteger_pdf import ProtegerPdf
from lectorpdf.core.use_cases.rellenar_campo import RellenarCampo
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.core.use_cases.unir_pdf import UnirPdf
from lectorpdf.core.use_cases.verificar_firmas import VerificarFirmas
from lectorpdf.ui import recientes
from lectorpdf.ui.about_dialog import AboutDialog
from lectorpdf.ui.banda_firmado import BandaFirmado
from lectorpdf.ui.busqueda.barra_busqueda import BarraBusqueda
from lectorpdf.ui.busqueda.busqueda_layer import BusquedaLayer
from lectorpdf.ui.enlaces.enlaces_layer import EnlacesLayer
from lectorpdf.ui.forms.form_layer import FormLayer
from lectorpdf.ui.herramientas.dividir_dialog import DividirDialog
from lectorpdf.ui.herramientas.unir_dialog import UnirDialog
from lectorpdf.ui.impresion.impresion import imprimir_documento
from lectorpdf.ui.outline.outline_panel import OutlinePanel
from lectorpdf.ui.seleccion.seleccion_layer import SeleccionLayer
from lectorpdf.ui.signature.biblioteca_firmas import (
    BibliotecaFirmas,
    directorio_por_defecto,
)
from lectorpdf.ui.signature.digital_seal_layer import DigitalSealLayer
from lectorpdf.ui.signature.digital_signature_dialog import DigitalSignatureDialog
from lectorpdf.ui.signature.signature_dialog import SignatureDialog
from lectorpdf.ui.signature.signature_layer import SignatureLayer
from lectorpdf.ui.signature.verification_panel import VerificationPanel
from lectorpdf.ui.tareas import ResultadoTarea, ejecutar_con_progreso
from lectorpdf.ui.theme.estilos import (
    aplicar_tema,
    cargar_tema_preferido,
    guardar_preferencia_tema,
)
from lectorpdf.ui.theme.iconos import icono
from lectorpdf.ui.theme.marca import NOMBRE_APP, ruta_icono_app
from lectorpdf.ui.theme.tokens import TEMA_CLARO, TEMA_OSCURO
from lectorpdf.ui.thumbnails.thumbnail_panel import ThumbnailPanel
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_TITULO_BASE = NOMBRE_APP
_ORG = "lectorpdf"
_APP = "lectorpdf"
_CLAVE_DOBLE = "vista/doble_pagina"
_CLAVE_MODO_AJUSTE = "vista/modo_ajuste"
_CLAVE_RECIENTES = "archivo/recientes"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        # Raíz de composición: un registro compartido para todos los adaptadores.
        self._registro = RegistroDocumentos()
        self._repositorio = PyMuPDFDocumentRepository(self._registro)
        self._servicio_form = PyMuPDFFormService(self._registro)
        self._servicio_estampado = PyMuPDFEstampadoService(self._registro)
        self._servicio_firma = PyHankoSignatureService(self._registro)
        self._servicio_herr = PyMuPDFHerramientas(self._registro)
        self._servicio_contenido = PyMuPDFContenido(self._registro)

        self._abrir = AbrirDocumento(self._repositorio)
        self._renderizar = RenderizarPagina(self._repositorio)
        self._listar = ListarCampos(self._servicio_form)
        self._rellenar = RellenarCampo(self._servicio_form)
        self._guardar_form = GuardarFormulario(self._servicio_form)
        self._estampar = EstamparFirma(self._servicio_estampado)
        self._firmar_digital = FirmarDigitalmente(self._servicio_firma)
        self._verificar = VerificarFirmas(self._servicio_firma)
        self._unir = UnirPdf(self._servicio_herr)
        self._organizar = OrganizarPaginas(self._servicio_herr)
        self._dividir = DividirPdf(self._servicio_herr)
        self._proteger = ProtegerPdf(self._servicio_herr)
        self._desproteger = DesprotegerPdf(self._servicio_herr)
        self._comprimir = ComprimirPdf(self._servicio_herr)
        self._exportar_png = ExportarImagenes(self._servicio_herr)
        self._exportar_texto = ExportarTexto(self._servicio_herr)
        self._buscar_contenido = BuscarEnDocumento(self._servicio_contenido)
        self._obtener_palabras = ObtenerPalabras(self._servicio_contenido)
        self._obtener_indice = ObtenerIndice(self._servicio_contenido)
        self._obtener_enlaces = ObtenerEnlaces(self._servicio_contenido)

        self._documento: Documento | None = None
        self._tema = cargar_tema_preferido()
        self._prefs = QSettings(_ORG, _APP)
        self._acciones_icono: list[tuple[QAction, str]] = []

        # Estado de búsqueda del documento activo (se limpia al abrir/cerrar).
        self._coincidencias: tuple[Coincidencia, ...] = ()
        self._indice_coincidencia = -1
        self._termino_busqueda = ""
        self._mayus_busqueda = False

        self._visor = ViewerWidget(self._renderizar)
        self._miniaturas = ThumbnailPanel(self._renderizar)
        self._outline = OutlinePanel()
        self._capa_form = FormLayer(self._visor, self._rellenar)
        self._capa_firma = SignatureLayer(self._visor, self._estampar)
        self._capa_sello = DigitalSealLayer(self._visor, self._firmar_digital)
        self._capa_busqueda = BusquedaLayer(self._visor)
        self._capa_seleccion = SeleccionLayer(self._visor, self._obtener_palabras)
        # Después de la selección: su filtro tiene prioridad sobre el ratón.
        self._capa_enlaces = EnlacesLayer(self._visor, self._obtener_enlaces)
        self._barra_busqueda = BarraBusqueda()
        self._barra_busqueda.hide()
        self._banda_firmado = BandaFirmado()
        self._banda_firmado.hide()
        self._biblioteca = BibliotecaFirmas(directorio_por_defecto())
        self.setCentralWidget(self._construir_central())

        self._construir_dock_miniaturas()
        self._panel_verificacion = VerificationPanel()
        self._construir_dock_verificacion()
        self._etiqueta_pagina = QLabel("—")
        self._construir_barra()
        self._construir_menu()
        self._conectar_senales()
        self._construir_atajos()

        self._aplicar_tema_actual()
        self._restaurar_modos_de_vista()
        self.setAcceptDrops(True)
        self.setWindowTitle(_TITULO_BASE)
        self._aplicar_icono_ventana()
        self.resize(1100, 1000)

    def _aplicar_icono_ventana(self) -> None:
        ruta = ruta_icono_app()
        if ruta is not None:
            self.setWindowIcon(QIcon(str(ruta)))

    def _aplicar_tema_actual(self) -> None:
        """Aplica el tema (QSS + fondo del visor + iconos) desde self._tema, que
        es la única fuente de verdad del tema en la ventana."""
        app = QApplication.instance()
        if isinstance(app, QApplication):
            aplicar_tema(app, self._tema)
        self._visor.aplicar_fondo(self._tema.canvas)
        for accion, nombre_icono in self._acciones_icono:
            accion.setIcon(icono(nombre_icono, self._tema.text))
        self._barra_busqueda.recolorear(self._tema.text)

    # -- Construcción de la UI ----------------------------------------------

    def _construir_central(self) -> QWidget:
        """Apila la barra de búsqueda (oculta) sobre el visor en el área central."""
        central = QWidget()
        central.setObjectName("centralWidget")
        disposicion = QVBoxLayout(central)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(self._banda_firmado)
        disposicion.addWidget(self._barra_busqueda)
        disposicion.addWidget(self._visor, 1)
        return central

    def _construir_atajos(self) -> None:
        """Atajos de teclado a nivel de ventana (se ampliará en la tarea 13)."""
        QShortcut(QKeySequence.StandardKey.Find, self, self._activar_busqueda)
        QShortcut(QKeySequence.StandardKey.FindNext, self, self._busqueda_siguiente)
        QShortcut(
            QKeySequence.StandardKey.FindPrevious, self, self._busqueda_anterior
        )
        QShortcut(QKeySequence("Ctrl+G"), self, self._ir_a_pagina_dialogo)
        QShortcut(QKeySequence.StandardKey.Print, self, self._imprimir)
        QShortcut(QKeySequence("F11"), self, self._conmutar_pantalla_completa)

    def _construir_dock_miniaturas(self) -> None:
        self._panel_lateral = QTabWidget()
        self._panel_lateral.addTab(self._miniaturas, "Miniaturas")
        self._idx_tab_indice = self._panel_lateral.addTab(self._outline, "Índice")
        self._panel_lateral.setTabVisible(self._idx_tab_indice, False)  # sin outline

        dock = QDockWidget("Navegación", self)
        dock.setWidget(self._panel_lateral)
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
        self._accion_icono(barra, "search", "Buscar (Ctrl+F)", self._activar_busqueda)
        self._accion_icono(barra, "print", "Imprimir (Ctrl+P)", self._imprimir)
        barra.addSeparator()
        self._accion_icono(barra, "zoom-out", "Alejar", self._visor.zoom_alejar)
        self._accion_icono(barra, "zoom-in", "Acercar", self._visor.zoom_acercar)
        self._accion_icono(barra, "fit-width", "Ajustar ancho", self._visor.ajustar_a_ancho)
        self._accion_icono(barra, "fit-page", "Ajustar página", self._visor.ajustar_a_pagina)
        self._accion_doble = self._accion_conmutable(
            barra, "page-double", "Doble página", self._conmutar_doble
        )
        self._accion_icono(barra, "rotate", "Rotar vista", lambda: self._visor.rotar_vista(90))
        self._accion_icono(
            barra, "fullscreen", "Pantalla completa (F11)", self._conmutar_pantalla_completa
        )
        barra.addSeparator()
        self._accion_icono(barra, "sign-draw", "Dibujar y estampar firma", self._iniciar_firma)
        self._accion_icono(barra, "sign-cert", "Firmar con certificado", self._firmar_digitalmente)
        self._accion(barra, "✓ Colocar", self._confirmar_firma)
        self._accion(barra, "✗ Cancelar", self._cancelar_colocacion)
        barra.addSeparator()
        self._accion_icono(barra, "verify", "Verificar firmas", self._verificar_firmas)
        barra.addSeparator()
        self._accion(barra, "Cambiar tema", self._conmutar_tema)
        self._accion(barra, "Acerca de", self._mostrar_acerca_de)
        barra.addWidget(self._etiqueta_pagina)

    def _construir_menu(self) -> None:
        self._construir_menu_archivo()
        menu = self.menuBar().addMenu("Herramientas")
        self._accion_menu(menu, "Unir PDF…", self._menu_unir)
        self._accion_menu(menu, "Dividir PDF…", self._menu_dividir)
        menu.addSeparator()
        self._accion_menu(menu, "Proteger con contraseña…", self._menu_proteger)
        self._accion_menu(menu, "Quitar contraseña…", self._menu_desproteger)
        menu.addSeparator()
        self._accion_menu(menu, "Comprimir…", self._menu_comprimir)
        menu.addSeparator()
        self._accion_menu(menu, "Exportar a PNG…", self._menu_exportar_png)
        self._accion_menu(menu, "Exportar a texto…", self._menu_exportar_texto)

    def _construir_menu_archivo(self) -> None:
        menu = self.menuBar().addMenu("Archivo")
        self._accion_menu(menu, "Abrir…", self._abrir_por_dialogo, "Ctrl+O")
        self._menu_recientes = menu.addMenu("Abrir recientes")
        self._reconstruir_menu_recientes()
        menu.addSeparator()
        self._accion_menu(menu, "Guardar", self._guardar, "Ctrl+S")
        self._accion_menu(menu, "Guardar como…", self._guardar_como, "Ctrl+Shift+S")
        self._accion_menu(menu, "Guardar una copia…", self._guardar_copia)
        menu.addSeparator()
        self._accion_menu(menu, "Imprimir…", self._imprimir, "Ctrl+P")
        self._accion_menu(menu, "Vista previa de impresión…", self._vista_previa_impresion)
        menu.addSeparator()
        self._accion_menu(menu, "Salir", self.close, "Ctrl+Q")

    def _accion_menu(
        self,
        menu: QMenu,
        texto: str,
        callback: Callable[[], object],
        atajo: str | None = None,
    ) -> QAction:
        accion = QAction(texto, self)
        accion.triggered.connect(callback)
        if atajo is not None:
            accion.setShortcut(QKeySequence(atajo))
        menu.addAction(accion)
        return accion

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

    def _accion_conmutable(
        self,
        barra: QToolBar,
        nombre_icono: str,
        tooltip: str,
        callback: Callable[[bool], None],
    ) -> QAction:
        accion = QAction(icono(nombre_icono, self._tema.text), tooltip, self)
        accion.setToolTip(tooltip)
        accion.setCheckable(True)
        accion.toggled.connect(callback)
        barra.addAction(accion)
        self._acciones_icono.append((accion, nombre_icono))
        return accion

    def _conectar_senales(self) -> None:
        self._visor.pagina_cambiada.connect(self._miniaturas.seleccionar_pagina)
        self._visor.pagina_cambiada.connect(self._actualizar_etiqueta)
        self._miniaturas.pagina_seleccionada.connect(self._visor.ir_a_pagina)
        self._miniaturas.rotar_solicitado.connect(self._rotar_pagina)
        self._miniaturas.eliminar_solicitado.connect(self._eliminar_pagina)
        self._miniaturas.mover_solicitado.connect(self._mover_pagina)
        self._outline.pagina_seleccionada.connect(self._visor.ir_a_pagina)
        self._capa_enlaces.navegar_interno.connect(self._visor.ir_a_pagina)
        self._capa_enlaces.abrir_externo.connect(self._confirmar_abrir_url)
        self._visor.modo_ajuste_cambiado.connect(self._guardar_modo_ajuste)
        self._barra_busqueda.buscar.connect(self._ejecutar_busqueda)
        self._barra_busqueda.siguiente.connect(self._busqueda_siguiente)
        self._barra_busqueda.anterior.connect(self._busqueda_anterior)
        self._barra_busqueda.cerrada.connect(self._cerrar_busqueda)
        self._banda_firmado.copia_solicitada.connect(self._guardar_copia)

    # -- Acciones -----------------------------------------------------------

    def abrir_ruta(self, ruta: Path) -> Documento:
        documento = self._abrir.ejecutar(ruta)
        self._documento = documento
        self._cerrar_busqueda()  # descarta resaltados/estado del documento previo
        self._capa_seleccion.set_documento(documento)
        self._capa_enlaces.set_documento(documento)
        self._visor.set_documento(documento)
        self._miniaturas.set_documento(documento)
        self._cargar_formulario(documento)
        self._cargar_indice(documento)
        self._actualizar_banda_firmado()
        self._registrar_reciente(ruta)
        nombre = documento.titulo or ruta.name
        self.setWindowTitle(f"{nombre} — {_TITULO_BASE}")
        self._actualizar_etiqueta(0)
        return documento

    # -- Archivo: recientes, guardar como/copia, banda de firmado -----------

    def _recientes(self) -> list[str]:
        valor = self._prefs.value(_CLAVE_RECIENTES, [])
        if isinstance(valor, list):
            return [str(v) for v in valor]
        return [str(valor)] if valor else []

    def _registrar_reciente(self, ruta: Path) -> None:
        lista = recientes.anadir(self._recientes(), str(ruta))
        self._prefs.setValue(_CLAVE_RECIENTES, lista)
        self._reconstruir_menu_recientes()

    def _reconstruir_menu_recientes(self) -> None:
        self._menu_recientes.clear()
        lista = self._recientes()
        if not lista:
            vacio = self._menu_recientes.addAction("(sin documentos recientes)")
            vacio.setEnabled(False)
            return
        for ruta in lista:
            accion = self._menu_recientes.addAction(recientes.elidir(ruta))
            accion.setToolTip(ruta)
            accion.triggered.connect(
                lambda _=False, r=ruta: self.abrir_ruta_con_aviso(Path(r))
            )
        self._menu_recientes.addSeparator()
        self._menu_recientes.addAction("Limpiar lista").triggered.connect(
            self._limpiar_recientes
        )

    def _limpiar_recientes(self) -> None:
        self._prefs.remove(_CLAVE_RECIENTES)
        self._reconstruir_menu_recientes()

    def _guardar_como(self) -> None:
        doc = self._documento
        if doc is None:
            return
        destino_str, _ = QFileDialog.getSaveFileName(
            self, "Guardar como", doc.ruta.name, "Documentos PDF (*.pdf)"
        )
        if not destino_str:
            return
        try:
            self._guardar_form.ejecutar(doc, Path(destino_str))
        except Exception as exc:  # errores de E/S de PyMuPDF al guardar
            QMessageBox.warning(self, "No se pudo guardar", str(exc))
            return
        self.abrir_ruta_con_aviso(Path(destino_str))  # trabaja sobre el nuevo

    def _guardar_copia(self) -> None:
        """Guarda una copia sin cambiar de documento. Es la vía de escape para
        obtener una copia de un documento firmado (que no se puede editar)."""
        doc = self._documento
        if doc is None:
            return
        destino_str, _ = QFileDialog.getSaveFileName(
            self, "Guardar una copia", f"copia_{doc.ruta.name}", "Documentos PDF (*.pdf)"
        )
        if not destino_str:
            return
        try:
            self._guardar_form.ejecutar(doc, Path(destino_str))
        except Exception as exc:
            QMessageBox.warning(self, "No se pudo guardar la copia", str(exc))
            return
        QMessageBox.information(self, "Copia guardada", f"Copia guardada en:\n{destino_str}")

    def _actualizar_banda_firmado(self) -> None:
        doc = self._documento
        firmado = doc is not None and self._guardar_form.esta_firmado(doc)
        self._banda_firmado.setVisible(firmado)

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

    def _cargar_indice(self, documento: Documento) -> None:
        """Puebla el árbol de índice y muestra su pestaña solo si hay outline."""
        entradas = self._obtener_indice.ejecutar(documento)
        tiene = self._outline.set_entradas(entradas)
        self._panel_lateral.setTabVisible(self._idx_tab_indice, tiene)

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
        self._actualizar_banda_firmado()
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

    # -- Organizar páginas (desde el panel de miniaturas) -------------------

    def _rotar_pagina(self, indice: int, grados: int) -> None:
        self._aplicar_organizacion(lambda d: self._organizar.rotar(d, indice, grados))

    def _eliminar_pagina(self, indice: int) -> None:
        self._aplicar_organizacion(lambda d: self._organizar.eliminar(d, indice))

    def _mover_pagina(self, origen: int, destino: int) -> None:
        self._aplicar_organizacion(lambda d: self._organizar.mover(d, origen, destino))

    def _aplicar_organizacion(
        self, operacion: Callable[[Documento], Documento]
    ) -> None:
        if self._documento is None:
            return
        try:
            nuevo = operacion(self._documento)
        except ErrorDominio as exc:
            QMessageBox.warning(self, "No se pudo organizar", str(exc))
            return
        self._documento = nuevo
        # La reorganización cambió las páginas: refrescar visor (con el zoom
        # actual, que invalida la caché de render), miniaturas y formulario.
        self._capa_seleccion.set_documento(nuevo)  # invalida el texto cacheado
        self._capa_enlaces.set_documento(nuevo)
        self._visor.set_documento(nuevo, self._visor.escala)
        self._miniaturas.set_documento(nuevo)
        self._cargar_formulario(nuevo)
        self._cargar_indice(nuevo)

    # -- Herramientas -------------------------------------------------------

    def _menu_unir(self) -> None:
        ruta_inicial = self._documento.ruta if self._documento is not None else None
        dialogo = UnirDialog(self, ruta_inicial)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        rutas = dialogo.rutas()
        if len(rutas) < 2:
            QMessageBox.information(self, "Unir", "Elige al menos dos ficheros.")
            return
        if not self._asegurar_guardado_si_incluido(rutas):
            return
        destino_str, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF unido", "unido.pdf", "Documentos PDF (*.pdf)"
        )
        if not destino_str:
            return
        destino = Path(destino_str)
        res = ejecutar_con_progreso(
            self, "Uniendo PDF…", lambda p: self._unir.ejecutar(rutas, destino, p)
        )
        self._tras_tarea(res, f"PDF unido guardado en:\n{destino}")

    def _asegurar_guardado_si_incluido(self, rutas: list[Path]) -> bool:
        """Si el documento abierto está en la lista y tiene cambios sin guardar,
        ofrece guardarlo antes de unir. Devuelve False si el usuario cancela."""
        doc = self._documento
        if doc is None or doc.ruta not in rutas:
            return True
        if not self._guardar_form.hay_cambios_sin_guardar(doc):
            return True
        respuesta = QMessageBox.question(
            self,
            "Cambios sin guardar",
            "El documento abierto está en la lista y tiene cambios sin guardar.\n"
            "Se unirá desde el fichero en disco. ¿Guardarlo antes?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Cancel,
        )
        if respuesta == QMessageBox.StandardButton.Save:
            self._guardar()
            return True
        return False

    def _tras_tarea(self, res: ResultadoTarea, mensaje_ok: str) -> None:
        if res.cancelado:
            return
        if res.error is not None:
            QMessageBox.warning(self, "No se pudo completar", str(res.error))
            return
        QMessageBox.information(self, "Hecho", mensaje_ok)

    def _documento_o_aviso(self, titulo: str) -> Documento | None:
        if self._documento is None:
            QMessageBox.information(self, titulo, "Abre un PDF primero.")
        return self._documento

    def _menu_dividir(self) -> None:
        doc = self._documento_o_aviso("Dividir")
        if doc is None:
            return
        dialogo = DividirDialog(self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        directorio = QFileDialog.getExistingDirectory(
            self, "Carpeta donde guardar las partes"
        )
        if not directorio:
            return
        salida = Path(directorio)

        if dialogo.es_por_pagina():
            res = ejecutar_con_progreso(
                self, "Dividiendo PDF…", lambda p: self._dividir.por_paginas(doc, salida)
            )
        else:
            try:
                rangos = dialogo.rangos()
            except ValueError as exc:
                QMessageBox.warning(self, "Rangos inválidos", str(exc))
                return
            res = ejecutar_con_progreso(
                self,
                "Dividiendo PDF…",
                lambda p: self._dividir.por_rangos(doc, rangos, salida),
            )
        if res.cancelado or res.error is not None:
            self._tras_tarea(res, "")
            return
        rutas = res.resultado if isinstance(res.resultado, list) else []
        QMessageBox.information(
            self, "Hecho", f"Generados {len(rutas)} ficheros en:\n{salida}"
        )

    def _menu_proteger(self) -> None:
        doc = self._documento_o_aviso("Proteger")
        if doc is None:
            return
        contrasena, ok = QInputDialog.getText(
            self, "Proteger con contraseña", "Contraseña:", QLineEdit.EchoMode.Password
        )
        if not ok or not contrasena:
            return
        destino_str, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF protegido", "protegido.pdf", "Documentos PDF (*.pdf)"
        )
        if not destino_str:
            return
        destino = Path(destino_str)
        res = ejecutar_con_progreso(
            self,
            "Protegiendo PDF…",
            lambda p: self._proteger.ejecutar(doc, destino, contrasena),
        )
        self._tras_tarea(res, f"PDF protegido guardado en:\n{destino}")

    def _menu_desproteger(self) -> None:
        ruta_str, _ = QFileDialog.getOpenFileName(
            self, "PDF protegido", "", "Documentos PDF (*.pdf)"
        )
        if not ruta_str:
            return
        ruta = Path(ruta_str)
        contrasena, ok = QInputDialog.getText(
            self, "Quitar contraseña", "Contraseña:", QLineEdit.EchoMode.Password
        )
        if not ok:
            return
        destino_str, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF sin protección", "sin_proteccion.pdf",
            "Documentos PDF (*.pdf)",
        )
        if not destino_str:
            return
        destino = Path(destino_str)
        res = ejecutar_con_progreso(
            self,
            "Quitando protección…",
            lambda p: self._desproteger.ejecutar(ruta, contrasena, destino),
        )
        self._tras_tarea(res, f"PDF sin protección guardado en:\n{destino}")

    def _menu_comprimir(self) -> None:
        doc = self._documento_o_aviso("Comprimir")
        if doc is None:
            return
        destino_str, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF comprimido", "comprimido.pdf", "Documentos PDF (*.pdf)"
        )
        if not destino_str:
            return
        destino = Path(destino_str)
        res = ejecutar_con_progreso(
            self, "Comprimiendo PDF…", lambda p: self._comprimir.ejecutar(doc, destino, p)
        )
        if res.cancelado or res.error is not None:
            self._tras_tarea(res, "")
            return
        r = res.resultado
        if isinstance(r, ResultadoCompresion):
            QMessageBox.information(
                self,
                "Hecho",
                f"Comprimido: {r.bytes_antes} → {r.bytes_despues} bytes "
                f"({r.porcentaje_reduccion:.1f}% menos)\n{destino}",
            )

    def _menu_exportar_png(self) -> None:
        doc = self._documento_o_aviso("Exportar a PNG")
        if doc is None:
            return
        dpi, ok = QInputDialog.getInt(
            self, "Exportar a PNG", "Resolución (DPI):", DPI_POR_DEFECTO, 30, 600
        )
        if not ok:
            return
        directorio = QFileDialog.getExistingDirectory(self, "Carpeta para las imágenes")
        if not directorio:
            return
        salida = Path(directorio)
        res = ejecutar_con_progreso(
            self,
            "Exportando a PNG…",
            lambda p: self._exportar_png.ejecutar(doc, salida, dpi, p),
        )
        if res.cancelado or res.error is not None:
            self._tras_tarea(res, "")
            return
        rutas = res.resultado if isinstance(res.resultado, list) else []
        QMessageBox.information(
            self, "Hecho", f"Exportadas {len(rutas)} imágenes en:\n{salida}"
        )

    def _menu_exportar_texto(self) -> None:
        doc = self._documento_o_aviso("Exportar a texto")
        if doc is None:
            return
        destino_str, _ = QFileDialog.getSaveFileName(
            self, "Guardar texto", "texto.txt", "Texto (*.txt)"
        )
        if not destino_str:
            return
        destino = Path(destino_str)
        res = ejecutar_con_progreso(
            self, "Exportando texto…", lambda p: self._exportar_texto.ejecutar(doc, destino)
        )
        self._tras_tarea(res, f"Texto exportado a:\n{destino}")

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
        self._tema = TEMA_CLARO if self._tema.es_oscuro else TEMA_OSCURO
        guardar_preferencia_tema(self._tema.nombre)
        self._aplicar_tema_actual()

    def _mostrar_acerca_de(self) -> None:
        AboutDialog(self._tema.es_oscuro, self).exec()

    def _actualizar_etiqueta(self, indice: int) -> None:
        documento = self._visor.documento
        total = documento.num_paginas if documento is not None else 0
        self._etiqueta_pagina.setText(f"Página {indice + 1} / {total}")

    # -- Navegación: ir a página y enlaces ----------------------------------

    def _ir_a_pagina_dialogo(self) -> None:
        if self._documento is None:
            return
        total = self._documento.num_paginas
        actual = self._visor.pagina_actual() + 1
        numero, ok = QInputDialog.getInt(
            self, "Ir a página", "Número de página:", actual, 1, total
        )
        if ok:
            self._visor.ir_a_pagina(numero - 1)

    def _confirmar_abrir_url(self, uri: str) -> None:
        """Los enlaces externos abren el navegador solo tras confirmación."""
        respuesta = QMessageBox.question(
            self,
            "Abrir enlace externo",
            f"¿Abrir este enlace en el navegador?\n\n{uri}",
            QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel,
        )
        if respuesta == QMessageBox.StandardButton.Open:
            QDesktopServices.openUrl(QUrl(uri))

    # -- Modos de vista -----------------------------------------------------

    def _conmutar_doble(self, activado: bool) -> None:
        self._visor.set_doble_pagina(activado)
        self._prefs.setValue(_CLAVE_DOBLE, activado)

    def _conmutar_pantalla_completa(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _guardar_modo_ajuste(self, nombre: str) -> None:
        self._prefs.setValue(_CLAVE_MODO_AJUSTE, nombre)

    def _restaurar_modos_de_vista(self) -> None:
        """Aplica las preferencias de doble página y modo de ajuste al arrancar."""
        doble = self._prefs.value(_CLAVE_DOBLE, False, type=bool)
        if doble:
            self._accion_doble.setChecked(True)  # dispara _conmutar_doble
        modo = str(self._prefs.value(_CLAVE_MODO_AJUSTE, "LIBRE"))
        self._visor.set_modo_ajuste(modo)

    # -- Impresión ----------------------------------------------------------

    def _imprimir(self) -> None:
        doc = self._documento
        if doc is None:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setFromTo(1, doc.num_paginas)  # habilita el rango en el diálogo
        dialogo = QPrintDialog(printer, self)
        dialogo.setOption(
            QAbstractPrintDialog.PrintDialogOption.PrintPageRange, True
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        primera = (printer.fromPage() or 1) - 1
        ultima = (printer.toPage() or doc.num_paginas) - 1
        imprimir_documento(printer, doc, self._renderizar, primera, ultima)

    def _vista_previa_impresion(self) -> None:
        doc = self._documento
        if doc is None:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialogo = QPrintPreviewDialog(printer, self)
        dialogo.paintRequested.connect(
            lambda pr: imprimir_documento(
                pr, doc, self._renderizar, 0, doc.num_paginas - 1
            )
        )
        dialogo.exec()

    # -- Búsqueda -----------------------------------------------------------

    def _activar_busqueda(self) -> None:
        if self._documento is None:
            return
        self._barra_busqueda.activar(self._termino_busqueda)

    def _ejecutar_busqueda(self, texto: str, coincidir_mayusculas: bool) -> None:
        doc = self._documento
        if doc is None:
            return
        if not texto:
            self._reiniciar_busqueda()
            self._barra_busqueda.mostrar_contador(0, 0)
            return
        # Mismo término y parámetros con resultados: solo avanzar, sin re-buscar.
        if (
            texto == self._termino_busqueda
            and coincidir_mayusculas == self._mayus_busqueda
            and self._coincidencias
        ):
            self._busqueda_siguiente()
            return
        res = ejecutar_con_progreso(
            self,
            "Buscando…",
            lambda p: self._buscar_contenido.ejecutar(
                doc, texto, coincidir_mayusculas, p
            ),
        )
        if res.cancelado or res.error is not None:
            return
        coincidencias = res.resultado if isinstance(res.resultado, tuple) else ()
        self._termino_busqueda = texto
        self._mayus_busqueda = coincidir_mayusculas
        self._coincidencias = coincidencias
        self._indice_coincidencia = 0 if coincidencias else -1
        self._capa_busqueda.set_coincidencias(coincidencias, self._indice_coincidencia)
        self._actualizar_contador()
        self._ir_a_coincidencia()

    def _busqueda_siguiente(self) -> None:
        self._mover_coincidencia(1)

    def _busqueda_anterior(self) -> None:
        self._mover_coincidencia(-1)

    def _mover_coincidencia(self, paso: int) -> None:
        if not self._coincidencias:
            return
        total = len(self._coincidencias)
        self._indice_coincidencia = (self._indice_coincidencia + paso) % total
        self._capa_busqueda.set_activa(self._indice_coincidencia)
        self._actualizar_contador()
        self._ir_a_coincidencia()

    def _ir_a_coincidencia(self) -> None:
        if not self._coincidencias or self._indice_coincidencia < 0:
            return
        coincidencia = self._coincidencias[self._indice_coincidencia]
        self._visor.centrar_en(coincidencia.pagina, coincidencia.rect_pt)

    def _actualizar_contador(self) -> None:
        total = len(self._coincidencias)
        actual = self._indice_coincidencia + 1 if total else 0
        self._barra_busqueda.mostrar_contador(actual, total)

    def _reiniciar_busqueda(self) -> None:
        """Descarta el estado y los resaltados de búsqueda (al abrir/cerrar)."""
        self._coincidencias = ()
        self._indice_coincidencia = -1
        self._termino_busqueda = ""
        self._capa_busqueda.limpiar()

    def _cerrar_busqueda(self) -> None:
        self._barra_busqueda.hide()
        self._reiniciar_busqueda()
        self._visor.setFocus()

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
