"""Vista de un documento abierto: visor, capas superpuestas, búsqueda y banda.

Encapsula todo el estado *por documento* para poder tener varios abiertos en
pestañas. Los casos de uso son compartidos (operan por id de documento), así que
se le inyectan; la vista solo posee los widgets y el estado de su documento.
La ventana principal conserva la barra de herramientas, los menús y los paneles
(miniaturas, índice, verificación), que siguen a la pestaña activa.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from lectorpdf.core.domain.contenido import Coincidencia
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.buscar_en_documento import BuscarEnDocumento
from lectorpdf.core.use_cases.estampar_firma import EstamparFirma
from lectorpdf.core.use_cases.firmar_digitalmente import FirmarDigitalmente
from lectorpdf.core.use_cases.obtener_enlaces import ObtenerEnlaces
from lectorpdf.core.use_cases.obtener_palabras import ObtenerPalabras
from lectorpdf.core.use_cases.rellenar_campo import RellenarCampo
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.banda_firmado import BandaFirmado
from lectorpdf.ui.busqueda.barra_busqueda import BarraBusqueda
from lectorpdf.ui.busqueda.busqueda_layer import BusquedaLayer
from lectorpdf.ui.enlaces.enlaces_layer import EnlacesLayer
from lectorpdf.ui.forms.form_layer import FormLayer
from lectorpdf.ui.seleccion.seleccion_layer import SeleccionLayer
from lectorpdf.ui.signature.digital_seal_layer import DigitalSealLayer
from lectorpdf.ui.signature.signature_layer import SignatureLayer
from lectorpdf.ui.tareas import ejecutar_con_progreso
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget


class VistaDocumento(QWidget):
    #: Página (0-based) en foco cambió en esta vista.
    pagina_cambiada = Signal(int)
    #: El modo de ajuste del visor cambió (para persistirlo globalmente).
    modo_ajuste_cambiado = Signal(str)
    #: La escala (zoom) del visor cambió.
    escala_cambiada = Signal(float)
    #: Enlace externo pulsado: la ventana confirma antes de abrir el navegador.
    abrir_externo = Signal(str)
    #: El usuario pide guardar una copia editable del documento firmado.
    copia_solicitada = Signal()

    def __init__(
        self,
        *,
        render: RenderizarPagina,
        rellenar: RellenarCampo,
        estampar: EstamparFirma,
        firmar_digital: FirmarDigitalmente,
        buscar: BuscarEnDocumento,
        palabras: ObtenerPalabras,
        enlaces: ObtenerEnlaces,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._buscar = buscar
        self._documento: Documento | None = None

        self.visor = ViewerWidget(render)
        self.capa_form = FormLayer(self.visor, rellenar)
        self.capa_firma = SignatureLayer(self.visor, estampar)
        self.capa_sello = DigitalSealLayer(self.visor, firmar_digital)
        self.capa_busqueda = BusquedaLayer(self.visor)
        self.capa_seleccion = SeleccionLayer(self.visor, palabras)
        self.capa_enlaces = EnlacesLayer(self.visor, enlaces)
        self.barra_busqueda = BarraBusqueda()
        self.barra_busqueda.hide()
        self.banda_firmado = BandaFirmado()
        self.banda_firmado.hide()

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(self.banda_firmado)
        disposicion.addWidget(self.barra_busqueda)
        disposicion.addWidget(self.visor, 1)

        # Estado de búsqueda de este documento.
        self._coincidencias: tuple[Coincidencia, ...] = ()
        self._indice_coincidencia = -1
        self._termino_busqueda = ""
        self._mayus_busqueda = False

        self.visor.pagina_cambiada.connect(self.pagina_cambiada)
        self.visor.modo_ajuste_cambiado.connect(self.modo_ajuste_cambiado)
        self.visor.escala_cambiada.connect(self.escala_cambiada)
        self.capa_enlaces.navegar_interno.connect(self.visor.ir_a_pagina)
        self.capa_enlaces.abrir_externo.connect(self.abrir_externo)
        self.banda_firmado.copia_solicitada.connect(self.copia_solicitada)
        self.barra_busqueda.buscar.connect(self._ejecutar_busqueda)
        self.barra_busqueda.siguiente.connect(self._busqueda_siguiente)
        self.barra_busqueda.anterior.connect(self._busqueda_anterior)
        self.barra_busqueda.cerrada.connect(self._cerrar_busqueda)

    @property
    def documento(self) -> Documento | None:
        return self._documento

    def set_documento(self, documento: Documento) -> None:
        self._documento = documento
        self._cerrar_busqueda()
        self.capa_seleccion.set_documento(documento)
        self.capa_enlaces.set_documento(documento)
        self.visor.set_documento(documento)

    def recolorear(self, color_hex: str) -> None:
        self.barra_busqueda.recolorear(color_hex)

    def aplicar_fondo(self, color_hex: str) -> None:
        self.visor.aplicar_fondo(color_hex)

    def mostrar_banda_firmado(self, firmado: bool) -> None:
        self.banda_firmado.setVisible(firmado)

    def seleccionar_todo(self) -> None:
        """Selecciona todo el texto de la página actual."""
        self.capa_seleccion.seleccionar_todo(self.visor.pagina_actual())

    # -- Búsqueda -----------------------------------------------------------

    def activar_busqueda(self) -> None:
        if self._documento is None:
            return
        self.barra_busqueda.activar(self._termino_busqueda)

    def _ejecutar_busqueda(self, texto: str, coincidir_mayusculas: bool) -> None:
        doc = self._documento
        if doc is None:
            return
        if not texto:
            self._reiniciar_busqueda()
            self.barra_busqueda.mostrar_contador(0, 0)
            return
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
            lambda p: self._buscar.ejecutar(doc, texto, coincidir_mayusculas, p),
        )
        if res.cancelado or res.error is not None:
            return
        coincidencias = res.resultado if isinstance(res.resultado, tuple) else ()
        self._termino_busqueda = texto
        self._mayus_busqueda = coincidir_mayusculas
        self._coincidencias = coincidencias
        self._indice_coincidencia = 0 if coincidencias else -1
        self.capa_busqueda.set_coincidencias(coincidencias, self._indice_coincidencia)
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
        self.capa_busqueda.set_activa(self._indice_coincidencia)
        self._actualizar_contador()
        self._ir_a_coincidencia()

    def _ir_a_coincidencia(self) -> None:
        if not self._coincidencias or self._indice_coincidencia < 0:
            return
        coincidencia = self._coincidencias[self._indice_coincidencia]
        self.visor.centrar_en(coincidencia.pagina, coincidencia.rect_pt)

    def _actualizar_contador(self) -> None:
        total = len(self._coincidencias)
        actual = self._indice_coincidencia + 1 if total else 0
        self.barra_busqueda.mostrar_contador(actual, total)

    def _reiniciar_busqueda(self) -> None:
        self._coincidencias = ()
        self._indice_coincidencia = -1
        self._termino_busqueda = ""
        self.capa_busqueda.limpiar()

    def _cerrar_busqueda(self) -> None:
        self.barra_busqueda.hide()
        self._reiniciar_busqueda()
        self.visor.setFocus()
