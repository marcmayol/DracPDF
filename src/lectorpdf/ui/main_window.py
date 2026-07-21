"""Ventana principal. Actúa como raíz de composición: cablea el adaptador
PyMuPDF con los casos de uso y conecta el visor con el panel de miniaturas y la
barra de herramientas.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QMimeData, QPoint, QSettings, Qt, QUrl
from PySide6.QtGui import (
    QAction,
    QActionGroup,
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
from lectorpdf.core.use_cases.historial_formulario import HistorialFormulario
from lectorpdf.core.use_cases.listar_campos import ListarCampos
from lectorpdf.core.use_cases.obtener_enlaces import ObtenerEnlaces
from lectorpdf.core.use_cases.obtener_indice import ObtenerIndice
from lectorpdf.core.use_cases.obtener_palabras import ObtenerPalabras
from lectorpdf.core.use_cases.obtener_propiedades import ObtenerPropiedades
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
from lectorpdf.ui.propiedades_dialog import PropiedadesDialog
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
from lectorpdf.ui.theme.barra_titulo import aplicar_modo_oscuro, instalar_gestor
from lectorpdf.ui.theme.estilos import (
    aplicar_tema,
    cargar_tema_preferido,
    guardar_preferencia_tema,
)
from lectorpdf.ui.theme.iconos import icono
from lectorpdf.ui.theme.marca import NOMBRE_APP, ruta_icono_app
from lectorpdf.ui.theme.tokens import TEMA_CLARO, TEMA_OSCURO, Tema
from lectorpdf.ui.thumbnails.thumbnail_panel import ThumbnailPanel
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget
from lectorpdf.ui.vista_documento import VistaDocumento

_TITULO_BASE = NOMBRE_APP
_ORG = "lectorpdf"
_APP = "lectorpdf"
_CLAVE_DOBLE = "vista/doble_pagina"
_CLAVE_MODO_AJUSTE = "vista/modo_ajuste"
_CLAVE_RECIENTES = "archivo/recientes"
_CLAVE_SESION = "sesion/documentos"
_CLAVE_SESION_ACTIVA = "sesion/activa"
_CLAVE_RESTAURAR = "sesion/restaurar"


def _resolver(ruta: Path) -> Path:
    """Ruta canónica para comparar documentos (misma ruta = mismo documento)."""
    try:
        return ruta.resolve()
    except OSError:
        return ruta


class MainWindow(QMainWindow):
    def __init__(
        self, *, restaurar_sesion: bool = False, persistir_sesion: bool = False
    ) -> None:
        super().__init__()
        # Persistir la sesión (lista de documentos abiertos) al cerrar. Solo en
        # arranque en frío sin fichero: un arranque puntual con un adjunto no debe
        # sobrescribir la sesión de trabajo. El estado por documento (página/zoom)
        # se guarda siempre, con independencia de esto.
        self._persistir_sesion = persistir_sesion
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
        self._historial_form = HistorialFormulario(self._servicio_form)
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
        self._obtener_propiedades = ObtenerPropiedades(self._servicio_contenido)

        self._tema = cargar_tema_preferido()
        self._prefs = QSettings(_ORG, _APP)
        self._acciones_icono: list[tuple[QAction, str]] = []
        self._sincronizando_doble = False  # evita recursión al sincronizar radios
        # Sincroniza la barra de título nativa (Windows) con el tema en cada
        # ventana que se muestre (principal, diálogos, mensajes). Un único gestor
        # por QApplication (no acumula filtros al crear varias ventanas).
        app_inicial = QApplication.instance()
        assert isinstance(app_inicial, QApplication)  # siempre hay QApplication
        self._gestor_barra = instalar_gestor(app_inicial, self._tema.es_oscuro)

        self._miniaturas = ThumbnailPanel(self._renderizar)
        self._outline = OutlinePanel()
        self._biblioteca = BibliotecaFirmas(directorio_por_defecto())
        self.setCentralWidget(self._construir_central())  # QTabWidget de vistas

        self._construir_dock_miniaturas()
        self._panel_verificacion = VerificationPanel()
        self._construir_dock_verificacion()
        self._etiqueta_pagina = QLabel("—")
        self._construir_barra()
        self._construir_menu()
        self._conectar_senales()
        self._construir_atajos()

        self._nueva_pestana_vacia()  # siempre hay al menos una pestaña
        self._aplicar_tema_actual()
        self._restaurar_modos_de_vista()
        self.setAcceptDrops(True)
        self.setWindowTitle(_TITULO_BASE)
        self._aplicar_icono_ventana()
        self.resize(1100, 1000)
        if restaurar_sesion:
            self._restaurar_sesion()

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
        for vista in self._vistas():
            vista.aplicar_fondo(self._tema.canvas)
            vista.recolorear(self._tema.text)
        for accion, nombre_icono in self._acciones_icono:
            accion.setIcon(icono(nombre_icono, self._tema.text))
        # Barra de título nativa: la ventana ahora, y las futuras vía el gestor.
        self._gestor_barra.set_oscuro(self._tema.es_oscuro)
        aplicar_modo_oscuro(self, self._tema.es_oscuro)

    # -- Proxies a la vista (pestaña) activa --------------------------------

    @property
    def _documento(self) -> Documento | None:
        return self._vista().documento

    @property
    def _visor(self) -> ViewerWidget:
        return self._vista().visor

    @property
    def _capa_form(self) -> FormLayer:
        return self._vista().capa_form

    @property
    def _capa_firma(self) -> SignatureLayer:
        return self._vista().capa_firma

    @property
    def _capa_sello(self) -> DigitalSealLayer:
        return self._vista().capa_sello

    @property
    def _capa_busqueda(self) -> BusquedaLayer:
        return self._vista().capa_busqueda

    @property
    def _capa_seleccion(self) -> SeleccionLayer:
        return self._vista().capa_seleccion

    @property
    def _capa_enlaces(self) -> EnlacesLayer:
        return self._vista().capa_enlaces

    @property
    def _barra_busqueda(self) -> BarraBusqueda:
        return self._vista().barra_busqueda

    @property
    def _banda_firmado(self) -> BandaFirmado:
        return self._vista().banda_firmado

    @property
    def _coincidencias(self) -> tuple[Coincidencia, ...]:
        return self._vista()._coincidencias

    @property
    def _indice_coincidencia(self) -> int:
        return self._vista()._indice_coincidencia

    # -- Construcción de la UI ----------------------------------------------

    def _construir_central(self) -> QWidget:
        """El área central es un QTabWidget: una VistaDocumento por pestaña."""
        self._pestanas = QTabWidget()
        self._pestanas.setObjectName("centralWidget")
        self._pestanas.setDocumentMode(True)
        self._pestanas.setTabsClosable(True)
        self._pestanas.setMovable(True)
        self._pestanas.tabCloseRequested.connect(self._cerrar_pestana)
        self._pestanas.currentChanged.connect(self._al_cambiar_pestana)
        return self._pestanas

    # -- Gestión de pestañas (multi-documento) ------------------------------

    def _nueva_vista(self) -> VistaDocumento:
        """Crea una VistaDocumento cableada y heredando los modos de vista."""
        vista = VistaDocumento(
            render=self._renderizar,
            rellenar=self._rellenar,
            estampar=self._estampar,
            firmar_digital=self._firmar_digital,
            buscar=self._buscar_contenido,
            palabras=self._obtener_palabras,
            enlaces=self._obtener_enlaces,
        )
        vista.recolorear(self._tema.text)
        vista.aplicar_fondo(self._tema.canvas)
        vista.visor.set_doble_pagina(self._accion_doble.isChecked())
        vista.visor.set_modo_ajuste(str(self._prefs.value(_CLAVE_MODO_AJUSTE, "LIBRE")))
        vista.visor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        vista.visor.customContextMenuRequested.connect(
            lambda pos, v=vista: self._menu_contextual_pagina(v, pos)
        )
        vista.pagina_cambiada.connect(self._al_cambiar_pagina)
        vista.modo_ajuste_cambiado.connect(self._guardar_modo_ajuste)
        vista.abrir_externo.connect(self._confirmar_abrir_url)
        vista.copia_solicitada.connect(self._guardar_copia)
        return vista

    def _nueva_pestana_vacia(self) -> VistaDocumento:
        vista = self._nueva_vista()
        indice = self._pestanas.addTab(vista, "Sin documento")
        self._pestanas.setCurrentIndex(indice)
        return vista

    def _vista(self) -> VistaDocumento:
        """Vista de la pestaña activa (siempre hay al menos una)."""
        widget = self._pestanas.currentWidget()
        assert isinstance(widget, VistaDocumento)
        return widget

    def _vistas(self) -> list[VistaDocumento]:
        vistas = []
        for i in range(self._pestanas.count()):
            widget = self._pestanas.widget(i)
            if isinstance(widget, VistaDocumento):
                vistas.append(widget)
        return vistas

    def _vista_para_cargar(self) -> VistaDocumento:
        """La pestaña activa si está vacía; si no, una pestaña nueva."""
        actual = self._vista()
        if actual.documento is None:
            return actual
        return self._nueva_pestana_vacia()

    def _indice_pestana_por_ruta(self, ruta: Path) -> int | None:
        objetivo = _resolver(ruta)
        for i, vista in enumerate(self._vistas()):
            doc = vista.documento
            if doc is not None and _resolver(doc.ruta) == objetivo:
                return i
        return None

    def _cerrar_pestana_actual(self) -> None:
        self._cerrar_pestana(self._pestanas.currentIndex())

    def _menu_contextual_pagina(self, vista: VistaDocumento, pos: QPoint) -> None:
        menu = self._construir_menu_contextual(vista)
        viewport = vista.visor.viewport()
        if viewport is not None:
            menu.exec(viewport.mapToGlobal(pos))

    def _construir_menu_contextual(self, vista: VistaDocumento) -> QMenu:
        """Menú contextual de la página. Aislado para poder testearlo sin exec."""
        menu = QMenu(self)
        copiar = menu.addAction("Copiar")
        copiar.setEnabled(bool(vista.capa_seleccion.texto_seleccionado()))
        copiar.triggered.connect(vista.capa_seleccion.copiar)
        menu.addSeparator()
        menu.addAction("Buscar…").triggered.connect(self._activar_busqueda)
        menu.addAction("Ir a página…").triggered.connect(self._ir_a_pagina_dialogo)
        menu.addSeparator()
        menu.addAction("Ajustar ancho").triggered.connect(self._ajustar_ancho)
        menu.addAction("Ajustar página").triggered.connect(self._ajustar_pagina)
        menu.addAction("Rotar a la derecha").triggered.connect(self._rotar_derecha)
        menu.addSeparator()
        menu.addAction("Imprimir…").triggered.connect(self._imprimir)
        menu.addAction("Propiedades…").triggered.connect(self._mostrar_propiedades)
        return menu

    def _cerrar_pestana(self, indice: int) -> None:
        vista = self._pestanas.widget(indice)
        if not isinstance(vista, VistaDocumento):
            return
        doc = vista.documento
        if doc is not None and not self._confirmar_cierre_documento(vista):
            return
        if doc is not None:
            self._guardar_estado_documento(doc, vista)
            self._registro.cerrar(doc.id)
        self._pestanas.removeTab(indice)
        vista.deleteLater()
        if self._pestanas.count() == 0:
            self._nueva_pestana_vacia()

    def _al_cambiar_pestana(self, _indice: int) -> None:
        """Sincroniza los paneles compartidos con la pestaña activa."""
        if self._pestanas.count() == 0:
            return
        vista = self._vista()
        doc = vista.documento
        if doc is None:
            self._miniaturas.limpiar()
            self._outline.set_entradas(())
            self._panel_lateral.setTabVisible(self._idx_tab_indice, False)
            self.setWindowTitle(_TITULO_BASE)
            self._etiqueta_pagina.setText("—")
            return
        self._miniaturas.set_documento(doc)
        self._miniaturas.seleccionar_pagina(vista.visor.pagina_actual())
        self._cargar_indice(doc)
        self._actualizar_banda_firmado()
        self.setWindowTitle(f"{doc.titulo or doc.ruta.name} — {_TITULO_BASE}")
        self._actualizar_etiqueta(vista.visor.pagina_actual())

    def _al_cambiar_pagina(self, indice: int) -> None:
        """Cambió la página en alguna vista; refleja solo si es la activa."""
        if self.sender() is not self._vista():
            return
        self._miniaturas.seleccionar_pagina(indice)
        self._actualizar_etiqueta(indice)

    def _construir_atajos(self) -> None:
        """Atajos que NO tienen entrada de menú (los demás llevan su atajo en la
        acción del menú, para no duplicarlos)."""
        QShortcut(QKeySequence.StandardKey.FindNext, self, self._busqueda_siguiente)
        QShortcut(
            QKeySequence.StandardKey.FindPrevious, self, self._busqueda_anterior
        )
        QShortcut(QKeySequence.StandardKey.Close, self, self._cerrar_pestana_actual)

    def _construir_dock_miniaturas(self) -> None:
        self._panel_lateral = QTabWidget()
        self._panel_lateral.addTab(self._miniaturas, "Miniaturas")
        self._idx_tab_indice = self._panel_lateral.addTab(self._outline, "Índice")
        self._panel_lateral.setTabVisible(self._idx_tab_indice, False)  # sin outline

        self._dock_navegacion = QDockWidget("Navegación", self)
        self._dock_navegacion.setWidget(self._panel_lateral)
        self._dock_navegacion.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, self._dock_navegacion
        )
        self._construir_acciones_paneles()

    def _construir_acciones_paneles(self) -> None:
        """Acciones conmutables (menú Ver) para mostrar los paneles Miniaturas
        (F7) e Índice (F8). Solo componen sobre el dock existente."""
        self._sincronizando_paneles = False
        self._accion_panel_miniaturas = QAction("Panel de miniaturas", self)
        self._accion_panel_miniaturas.setCheckable(True)
        self._accion_panel_miniaturas.setShortcut(QKeySequence("F7"))
        self._accion_panel_miniaturas.toggled.connect(self._conmutar_panel_miniaturas)
        self._accion_panel_indice = QAction("Índice del documento", self)
        self._accion_panel_indice.setCheckable(True)
        self._accion_panel_indice.setShortcut(QKeySequence("F8"))
        self._accion_panel_indice.toggled.connect(self._conmutar_panel_indice)
        # Activas incluso antes de estar en el menú (atajos F7/F8).
        self.addAction(self._accion_panel_miniaturas)
        self.addAction(self._accion_panel_indice)
        self._dock_navegacion.visibilityChanged.connect(
            lambda _=False: self._sincronizar_checks_paneles()
        )
        self._panel_lateral.currentChanged.connect(
            lambda _=0: self._sincronizar_checks_paneles()
        )
        self._sincronizar_checks_paneles()

    def _conmutar_panel_miniaturas(self, activado: bool) -> None:
        if self._sincronizando_paneles:
            return
        if activado:
            self._dock_navegacion.show()
            self._panel_lateral.setCurrentWidget(self._miniaturas)
        else:
            self._dock_navegacion.hide()
        self._sincronizar_checks_paneles()

    def _conmutar_panel_indice(self, activado: bool) -> None:
        if self._sincronizando_paneles:
            return
        if activado:
            self._dock_navegacion.show()
            self._panel_lateral.setCurrentWidget(self._outline)
        else:
            self._dock_navegacion.hide()
        self._sincronizar_checks_paneles()

    def _sincronizar_checks_paneles(self) -> None:
        """La marca refleja qué panel se ve: solo el de la pestaña activa cuando
        el dock está visible (mutuamente excluyentes; ninguno si está oculto)."""
        visible = not self._dock_navegacion.isHidden()
        actual = self._panel_lateral.currentWidget()
        self._sincronizando_paneles = True
        self._accion_panel_miniaturas.setChecked(visible and actual is self._miniaturas)
        self._accion_panel_indice.setChecked(visible and actual is self._outline)
        self._sincronizando_paneles = False

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
        self._accion_icono(barra, "page-prev", "Página anterior", self._pagina_anterior)
        self._accion_icono(barra, "page-next", "Página siguiente", self._pagina_siguiente)
        self._accion_icono(barra, "search", "Buscar (Ctrl+F)", self._activar_busqueda)
        self._accion_icono(barra, "print", "Imprimir (Ctrl+P)", self._imprimir)
        barra.addSeparator()
        self._accion_icono(barra, "zoom-out", "Alejar", self._zoom_alejar)
        self._accion_icono(barra, "zoom-in", "Acercar", self._zoom_acercar)
        self._accion_icono(barra, "fit-width", "Ajustar ancho", self._ajustar_ancho)
        self._accion_icono(barra, "fit-page", "Ajustar página", self._ajustar_pagina)
        self._accion_doble = self._accion_conmutable(
            barra, "page-double", "Doble página", self._conmutar_doble
        )
        self._accion_icono(barra, "rotate", "Rotar a la derecha", self._rotar_derecha)
        self._accion_icono(
            barra, "fullscreen", "Pantalla completa (F11)", self._conmutar_pantalla_completa
        )
        barra.addSeparator()
        self._accion_icono(barra, "sign-draw", "Dibujar y estampar firma", self._iniciar_firma)
        self._accion_icono(barra, "sign-cert", "Firmar con certificado", self._firmar_digitalmente)
        barra.addSeparator()
        self._accion_icono(barra, "verify", "Verificar firmas", self._verificar_firmas)
        barra.addWidget(self._etiqueta_pagina)
        self._construir_barra_firma()

    def _construir_barra_firma(self) -> None:
        """Barra contextual del modo de colocación de firma: oculta por defecto,
        visible solo mientras se coloca (no reflowa la barra principal)."""
        self.addToolBarBreak()
        self._barra_firma = QToolBar("Colocación de firma", self)
        self.addToolBar(self._barra_firma)
        self._accion_colocar = QAction("✓ Colocar", self)
        self._accion_colocar.triggered.connect(self._confirmar_firma)
        self._accion_cancelar = QAction("✗ Cancelar", self)
        self._accion_cancelar.triggered.connect(self._cancelar_colocacion)
        self._barra_firma.addAction(self._accion_colocar)
        self._barra_firma.addAction(self._accion_cancelar)
        self._barra_firma.setVisible(False)  # solo en modo colocación

    def _colocando_firma(self) -> bool:
        return self._capa_firma.colocando() or self._capa_sello.colocando()

    def _actualizar_controles_firma(self) -> None:
        """Muestra la barra contextual solo mientras se coloca una firma/sello."""
        self._barra_firma.setVisible(self._colocando_firma())

    def _construir_menu(self) -> None:
        # Barra de menús según el diseño Ladón: Archivo · Edición · Ver ·
        # Documento · Firmas · Ayuda (no hay "Herramientas").
        self._construir_menu_archivo()
        self._construir_menu_edicion()
        self._construir_menu_ver()
        self._construir_menu_documento()
        self._construir_menu_firmas()
        self._construir_menu_ayuda()

    def _construir_menu_edicion(self) -> None:
        menu = self.menuBar().addMenu("Edición")
        self._accion_menu(menu, "Deshacer", self._deshacer, "Ctrl+Z")
        self._accion_menu(menu, "Rehacer", self._rehacer, "Ctrl+Y")
        menu.addSeparator()
        self._accion_menu(menu, "Copiar", self._copiar_seleccion, "Ctrl+C")
        self._accion_menu(menu, "Seleccionar todo", self._seleccionar_todo, "Ctrl+E")
        menu.addSeparator()
        self._accion_menu(menu, "Buscar…", self._activar_busqueda, "Ctrl+F")
        self._accion_menu(menu, "Ir a página…", self._ir_a_pagina_dialogo, "Ctrl+G")

    def _construir_menu_ver(self) -> None:
        menu = self.menuBar().addMenu("Ver")
        # Una página / Doble página (radio exclusivo).
        grupo = QActionGroup(self)
        grupo.setExclusive(True)
        self._accion_una_pagina = QAction("Una página", self)
        self._accion_una_pagina.setCheckable(True)
        self._accion_una_pagina.setShortcut(QKeySequence("Ctrl+1"))
        self._accion_una_pagina.triggered.connect(lambda: self._set_doble(False))
        self._accion_doble_pagina = QAction("Doble página", self)
        self._accion_doble_pagina.setCheckable(True)
        self._accion_doble_pagina.setShortcut(QKeySequence("Ctrl+2"))
        self._accion_doble_pagina.triggered.connect(lambda: self._set_doble(True))
        grupo.addAction(self._accion_una_pagina)
        grupo.addAction(self._accion_doble_pagina)
        menu.addAction(self._accion_una_pagina)
        menu.addAction(self._accion_doble_pagina)
        menu.addSeparator()
        menu.addAction(self._accion_panel_miniaturas)  # F7
        menu.addAction(self._accion_panel_indice)  # F8
        menu.addSeparator()
        self._accion_menu(menu, "Ajustar a ancho", self._ajustar_ancho, "Ctrl+3")
        ajustar_pagina = self._accion_menu(
            menu, "Ajustar a página", self._ajustar_pagina, "Ctrl+4"
        )
        ajustar_pagina.setShortcuts(  # Ctrl+0 como alias (estándar de visores)
            [QKeySequence("Ctrl+4"), QKeySequence("Ctrl+0")]
        )
        self._accion_menu(menu, "Acercar", self._zoom_acercar, "Ctrl++")
        self._accion_menu(menu, "Alejar", self._zoom_alejar, "Ctrl+-")
        menu.addSeparator()
        submenu = menu.addMenu("Rotar vista")
        self._accion_menu(submenu, "Rotar a la derecha", self._rotar_derecha, "Ctrl+Shift+R")
        self._accion_menu(submenu, "Rotar a la izquierda", self._rotar_izquierda, "Ctrl+Shift+L")
        self._accion_menu(
            menu, "Pantalla completa", self._conmutar_pantalla_completa, "F11"
        )
        presentacion = self._accion_menu(menu, "Presentación", lambda: None, "Shift+F5")
        presentacion.setEnabled(False)  # fuera de alcance (como en el diseño)
        menu.addSeparator()
        self._construir_submenu_tema(menu)

    def _construir_submenu_tema(self, menu: QMenu) -> None:
        submenu = menu.addMenu("Tema")
        grupo = QActionGroup(self)
        grupo.setExclusive(True)
        self._accion_tema_claro = QAction("Claro", self)
        self._accion_tema_claro.setCheckable(True)
        self._accion_tema_claro.triggered.connect(lambda: self._aplicar_tema(TEMA_CLARO))
        self._accion_tema_oscuro = QAction("Oscuro", self)
        self._accion_tema_oscuro.setCheckable(True)
        self._accion_tema_oscuro.triggered.connect(
            lambda: self._aplicar_tema(TEMA_OSCURO)
        )
        grupo.addAction(self._accion_tema_claro)
        grupo.addAction(self._accion_tema_oscuro)
        submenu.addAction(self._accion_tema_claro)
        submenu.addAction(self._accion_tema_oscuro)
        self._sincronizar_acciones_tema()

    def _construir_menu_documento(self) -> None:
        menu = self.menuBar().addMenu("Documento")
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
        menu.addSeparator()
        self._accion_menu(menu, "Propiedades del documento…", self._mostrar_propiedades)

    def _construir_menu_firmas(self) -> None:
        menu = self.menuBar().addMenu("Firmas")
        self._accion_menu(menu, "Firmar (dibujar y estampar)…", self._iniciar_firma)
        self._accion_menu(menu, "Firmar con certificado…", self._firmar_digitalmente)
        menu.addSeparator()
        self._accion_menu(menu, "Verificar firmas…", self._verificar_firmas)

    def _construir_menu_ayuda(self) -> None:
        menu = self.menuBar().addMenu("Ayuda")
        self._accion_menu(menu, "Acerca de DracPDF", self._mostrar_acerca_de)

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
        accion_sesion = QAction("Restaurar sesión al arrancar", self)
        accion_sesion.setCheckable(True)
        accion_sesion.setChecked(
            bool(self._prefs.value(_CLAVE_RESTAURAR, True, type=bool))
        )
        accion_sesion.toggled.connect(self._conmutar_restaurar_sesion)
        menu.addAction(accion_sesion)
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
        # Solo los paneles compartidos; las señales por documento se cablean en
        # _nueva_vista (una VistaDocumento por pestaña).
        self._miniaturas.pagina_seleccionada.connect(self._ir_a_pagina_activa)
        self._miniaturas.rotar_solicitado.connect(self._rotar_pagina)
        self._miniaturas.eliminar_solicitado.connect(self._eliminar_pagina)
        self._miniaturas.mover_solicitado.connect(self._mover_pagina)
        self._outline.pagina_seleccionada.connect(self._ir_a_pagina_activa)

    def _ir_a_pagina_activa(self, indice: int) -> None:
        self._visor.ir_a_pagina(indice)

    # Reenvíos de la barra al visor de la pestaña activa (evaluados al pulsar).
    def _pagina_anterior(self) -> None:
        self._visor.pagina_anterior()

    def _pagina_siguiente(self) -> None:
        self._visor.pagina_siguiente()

    def _zoom_acercar(self) -> None:
        self._visor.zoom_acercar()

    def _zoom_alejar(self) -> None:
        self._visor.zoom_alejar()

    def _ajustar_ancho(self) -> None:
        self._visor.ajustar_a_ancho()

    def _ajustar_pagina(self) -> None:
        self._visor.ajustar_a_pagina()

    def _rotar_derecha(self) -> None:
        self._visor.rotar_vista(90)

    def _rotar_izquierda(self) -> None:
        self._visor.rotar_vista(-90)

    # -- Acciones -----------------------------------------------------------

    def abrir_ruta(self, ruta: Path) -> Documento:
        # Si el documento ya está abierto, se activa su pestaña (no se duplica).
        indice_existente = self._indice_pestana_por_ruta(ruta)
        if indice_existente is not None:
            self._pestanas.setCurrentIndex(indice_existente)
            existente = self._vista().documento
            assert existente is not None
            return existente

        documento = self._abrir.ejecutar(ruta)
        vista = self._vista_para_cargar()
        vista.set_documento(documento)
        indice = self._pestanas.indexOf(vista)
        self._pestanas.setTabText(indice, documento.titulo or ruta.name)
        self._miniaturas.set_documento(documento)
        self._cargar_formulario(documento)
        self._cargar_indice(documento)
        self._actualizar_banda_firmado()
        self._registrar_reciente(ruta)
        self._restaurar_estado_documento(documento, vista)
        nombre = documento.titulo or ruta.name
        self.setWindowTitle(f"{nombre} — {_TITULO_BASE}")
        self._actualizar_etiqueta(vista.visor.pagina_actual())
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

    def _mostrar_propiedades(self) -> None:
        doc = self._documento
        if doc is None:
            return
        propiedades = self._obtener_propiedades.ejecutar(doc)
        PropiedadesDialog(propiedades, doc.ruta, self).exec()

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
            self._actualizar_controles_firma()  # entra en modo colocación

    def _confirmar_firma(self) -> None:
        if self._capa_sello.colocando():
            try:
                self._capa_sello.confirmar()
            except ErrorDominio as exc:
                QMessageBox.warning(self, "No se pudo firmar", str(exc))
                return
            self._tras_firmar()
            self._actualizar_controles_firma()
            return
        try:
            self._capa_firma.confirmar()
        except ErrorDominio as exc:
            QMessageBox.warning(self, "No se pudo estampar la firma", str(exc))
        self._actualizar_controles_firma()

    def _cancelar_colocacion(self) -> None:
        self._capa_firma.cancelar()
        self._capa_sello.cancelar()
        self._actualizar_controles_firma()

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
            self._actualizar_controles_firma()  # entra en modo colocación
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
        # La reorganización cambió las páginas: refrescar la vista activa (con el
        # zoom actual, que invalida la caché de render), miniaturas y formulario.
        vista = self._vista()
        escala = vista.visor.escala
        vista.set_documento(nuevo)
        vista.visor.set_escala(escala)
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

    def _aplicar_tema(self, tema: Tema) -> None:
        """Cambia al tema dado (menú Ver → Tema) y sincroniza las acciones."""
        if tema is self._tema:
            return
        self._tema = tema
        guardar_preferencia_tema(self._tema.nombre)
        self._aplicar_tema_actual()
        self._sincronizar_acciones_tema()

    def _sincronizar_acciones_tema(self) -> None:
        self._accion_tema_claro.setChecked(not self._tema.es_oscuro)
        self._accion_tema_oscuro.setChecked(self._tema.es_oscuro)

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

    def _set_doble(self, activado: bool) -> None:
        """Fuente única del modo una/doble página: aplica a todas las vistas,
        persiste y sincroniza los controles (radio del menú + botón de la barra)."""
        for vista in self._vistas():
            vista.visor.set_doble_pagina(activado)
        self._prefs.setValue(_CLAVE_DOBLE, activado)
        self._sincronizar_doble(activado)

    def _sincronizar_doble(self, activado: bool) -> None:
        self._sincronizando_doble = True
        self._accion_doble.setChecked(activado)
        self._accion_una_pagina.setChecked(not activado)
        self._accion_doble_pagina.setChecked(activado)
        self._sincronizando_doble = False

    def _conmutar_doble(self, activado: bool) -> None:
        if self._sincronizando_doble:
            return
        self._set_doble(activado)

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

    # -- Búsqueda (delega en la vista activa) -------------------------------

    def _activar_busqueda(self) -> None:
        self._vista().activar_busqueda()

    def _ejecutar_busqueda(self, texto: str, coincidir_mayusculas: bool) -> None:
        self._vista()._ejecutar_busqueda(texto, coincidir_mayusculas)

    def _busqueda_siguiente(self) -> None:
        self._vista()._busqueda_siguiente()

    def _busqueda_anterior(self) -> None:
        self._vista()._busqueda_anterior()

    def _cerrar_busqueda(self) -> None:
        self._vista()._cerrar_busqueda()

    def _seleccionar_todo(self) -> None:
        self._vista().seleccionar_todo()

    def _copiar_seleccion(self) -> None:
        self._vista().capa_seleccion.copiar()

    # -- Deshacer / rehacer en formularios ----------------------------------

    def _deshacer(self) -> None:
        doc = self._documento
        if doc is not None and self._historial_form.deshacer(doc) is not None:
            self._cargar_formulario(doc)  # el documento es la fuente de verdad

    def _rehacer(self) -> None:
        doc = self._documento
        if doc is not None and self._historial_form.rehacer(doc) is not None:
            self._cargar_formulario(doc)

    def closeEvent(self, event: QCloseEvent) -> None:
        # Todas las pestañas con cambios sin guardar se resuelven en un aviso.
        for vista in self._vistas():
            if not self._confirmar_cierre_documento(vista, activar=True):
                event.ignore()
                return
        if self._persistir_sesion:  # solo en arranque en frío sin fichero
            self._guardar_sesion()
        for vista in self._vistas():  # el estado por documento se guarda siempre
            if vista.documento is not None:
                self._guardar_estado_documento(vista.documento, vista)
        event.accept()

    # -- Sesión y estado por documento (persistencia) -----------------------

    def _confirmar_cierre_documento(
        self, vista: VistaDocumento, activar: bool = False
    ) -> bool:
        """Ofrece guardar los cambios pendientes de una pestaña antes de cerrarla.
        Devuelve False solo si el usuario cancela."""
        doc = vista.documento
        if doc is None or not self._guardar_form.hay_cambios_sin_guardar(doc):
            return True
        if activar:
            self._pestanas.setCurrentWidget(vista)
        respuesta = QMessageBox.question(
            self,
            "Cambios sin guardar",
            f"«{doc.ruta.name}» tiene cambios sin guardar. ¿Guardar antes de cerrar?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if respuesta == QMessageBox.StandardButton.Save:
            try:
                self._guardar_form.ejecutar(doc)
            except Exception as exc:
                QMessageBox.warning(self, "No se pudo guardar", str(exc))
                return False
            return True
        return respuesta == QMessageBox.StandardButton.Discard

    def _clave_estado(self, ruta: Path) -> str:
        return hashlib.sha1(str(_resolver(ruta)).encode("utf-8")).hexdigest()[:16]

    def _guardar_estado_documento(self, doc: Documento, vista: VistaDocumento) -> None:
        clave = self._clave_estado(doc.ruta)
        self._prefs.setValue(f"estado/{clave}/pagina", vista.visor.pagina_actual())
        self._prefs.setValue(f"estado/{clave}/escala", vista.visor.escala)

    def _restaurar_estado_documento(
        self, doc: Documento, vista: VistaDocumento
    ) -> None:
        clave = self._clave_estado(doc.ruta)
        escala = self._prefs.value(f"estado/{clave}/escala")
        pagina = self._prefs.value(f"estado/{clave}/pagina")
        if escala is not None:
            vista.visor.set_escala(float(escala))
        if pagina is not None:
            vista.visor.ir_a_pagina(int(pagina))

    def _guardar_sesion(self) -> None:
        rutas = [
            str(v.documento.ruta) for v in self._vistas() if v.documento is not None
        ]
        self._prefs.setValue(_CLAVE_SESION, rutas)
        self._prefs.setValue(_CLAVE_SESION_ACTIVA, self._pestanas.currentIndex())

    def _restaurar_sesion(self) -> None:
        """Reabre los documentos de la sesión anterior (si está activado). Las
        rutas que ya no existen se omiten en silencio."""
        if not self._prefs.value(_CLAVE_RESTAURAR, True, type=bool):
            return
        valor = self._prefs.value(_CLAVE_SESION, [])
        rutas = valor if isinstance(valor, list) else []
        for ruta in rutas:
            p = Path(str(ruta))
            if p.exists():
                self.abrir_ruta_con_aviso(p)
        activa = self._prefs.value(_CLAVE_SESION_ACTIVA)
        if activa is not None and 0 <= int(activa) < self._pestanas.count():
            self._pestanas.setCurrentIndex(int(activa))

    def _conmutar_restaurar_sesion(self, activado: bool) -> None:
        self._prefs.setValue(_CLAVE_RESTAURAR, activado)

    # -- Instancia única ----------------------------------------------------

    def traer_al_frente(self) -> None:
        """Restaura y trae la ventana al frente (segunda invocación de la app).
        En Windows a veces solo parpadea la barra de tareas; el ciclo
        minimizar/restaurar es la mitigación habitual si ocurre."""
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

    def abrir_desde_instancia(self, ruta_str: str) -> None:
        """Otra invocación pidió abrir un documento en esta instancia."""
        if ruta_str:
            self.abrir_ruta_con_aviso(Path(ruta_str))
        self.traer_al_frente()

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
