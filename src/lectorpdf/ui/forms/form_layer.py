"""Capa de formularios sobre el visor.

Coloca un QGraphicsProxyWidget por campo, pero solo para las páginas visibles
(las que el visor tiene renderizadas, es decir, visibles ± 1), y los destruye al
salir de ese rango. Como el documento en memoria es la única fuente de verdad,
al recrear un proxy basta con leer el campo de nuevo: no hay valor pendiente que
custodiar.

Se apoya en dos señales del visor:
- `escena_reconstruida`: el visor vació la escena (apertura o zoom); los proxies
  previos ya están destruidos, así que solo hay que olvidar sus referencias.
- `vista_actualizada`: cambió el conjunto de páginas visibles o la escala; se
  sincronizan los proxies (crear/mover/eliminar).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsProxyWidget

from lectorpdf.core.domain.errores import ErrorDominio
from lectorpdf.core.domain.formularios import CampoFormulario, TipoCampo
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.rellenar_campo import RellenarCampo
from lectorpdf.ui.forms.coordenadas import rect_pdf_a_escena
from lectorpdf.ui.forms.widgets_campo import conectar_edicion, crear_widget
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_Z_CAMPOS = 2.0  # por encima de los pixmaps de página (z = 1)
_ESTADO_OFF = "Off"


class FormLayer:
    def __init__(
        self, visor: ViewerWidget, caso_rellenar: RellenarCampo | None = None
    ) -> None:
        self._visor = visor
        self._caso_rellenar = caso_rellenar
        self._documento: Documento | None = None
        self._campos_por_pagina: dict[int, list[CampoFormulario]] = {}
        self._proxies: dict[str, QGraphicsProxyWidget] = {}

        visor.escena_reconstruida.connect(self._al_reconstruir_escena)
        visor.vista_actualizada.connect(self._sincronizar)

    def set_campos(
        self,
        campos: tuple[CampoFormulario, ...],
        documento: Documento | None = None,
    ) -> None:
        self._documento = documento
        self._campos_por_pagina = {}
        for campo in campos:
            self._campos_por_pagina.setdefault(campo.pagina, []).append(campo)
        self._al_reconstruir_escena()  # descarta proxies previos
        self._sincronizar()

    def proxies(self) -> dict[str, QGraphicsProxyWidget]:
        return dict(self._proxies)

    def tiene_campos(self) -> bool:
        return bool(self._campos_por_pagina)

    def primera_pagina_con_campo(self) -> int | None:
        """Página (0-based) más temprana con algún campo, o None si no hay."""
        if not self._campos_por_pagina:
            return None
        return min(self._campos_por_pagina)

    # -- Sincronización -----------------------------------------------------

    def _al_reconstruir_escena(self) -> None:
        # La escena se vació: los proxies ya no existen, solo olvidamos las refs.
        self._proxies.clear()

    def _sincronizar(self) -> None:
        visibles = self._visor.indices_mostrados()

        for campo_id, proxy in list(self._proxies.items()):
            pagina = _pagina_de(campo_id)
            if pagina not in visibles:
                escena = proxy.scene()
                if escena is not None:
                    escena.removeItem(proxy)
                del self._proxies[campo_id]

        for pagina in visibles:
            for campo in self._campos_por_pagina.get(pagina, []):
                if campo.id in self._proxies:
                    self._posicionar(self._proxies[campo.id], campo)
                else:
                    self._crear_proxy(campo)

    def _crear_proxy(self, campo: CampoFormulario) -> None:
        escena = self._visor.scene()
        if escena is None:
            return
        widget = crear_widget(campo)
        if self._caso_rellenar is not None and self._documento is not None:
            conectar_edicion(widget, campo, self._hacer_escritor(campo))
        proxy = escena.addWidget(widget)
        proxy.setZValue(_Z_CAMPOS)
        self._proxies[campo.id] = proxy
        self._posicionar(proxy, campo)

    def _hacer_escritor(self, campo: CampoFormulario) -> Callable[[str], None]:
        def escritor(valor: str) -> None:
            self._escribir(campo, valor)

        return escritor

    def _escribir(self, campo: CampoFormulario, valor: str) -> None:
        if self._caso_rellenar is None or self._documento is None:
            return
        if valor == campo.valor:
            return  # sin cambio real
        try:
            self._caso_rellenar.ejecutar(self._documento, campo, valor)
        except ErrorDominio:
            return  # valor inválido o campo de solo lectura: se ignora
        self._actualizar_cache(campo, valor)

    def _actualizar_cache(self, campo: CampoFormulario, valor: str) -> None:
        """Refleja en la caché el nuevo valor (doc = fuente de verdad), de modo
        que un proxy recreado tras salir/entrar de rango muestre el valor actual.
        Al activar un radio, apaga en caché sus hermanos del mismo grupo."""
        lista = self._campos_por_pagina.get(campo.pagina, [])
        for i, c in enumerate(lista):
            if c.id == campo.id:
                lista[i] = replace(c, valor=valor)
            elif (
                campo.tipo == TipoCampo.RADIO
                and c.tipo == TipoCampo.RADIO
                and c.nombre == campo.nombre
                and valor == campo.estado_activado
            ):
                lista[i] = replace(c, valor=_ESTADO_OFF)

    def _posicionar(self, proxy: QGraphicsProxyWidget, campo: CampoFormulario) -> None:
        rect_pagina = self._visor.rect_pagina(campo.pagina)
        if rect_pagina is None:
            return
        r = rect_pdf_a_escena(
            campo.rect_pt,
            rect_pagina.left(),
            rect_pagina.top(),
            self._visor.escala,
        )
        proxy.setGeometry(QRectF(r.x, r.y, r.ancho, r.alto))


def _pagina_de(campo_id: str) -> int:
    return int(campo_id.split(":", 1)[0])
