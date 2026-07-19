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

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsProxyWidget

from lectorpdf.core.domain.formularios import CampoFormulario
from lectorpdf.ui.forms.coordenadas import rect_pdf_a_escena
from lectorpdf.ui.forms.widgets_campo import crear_widget
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget

_Z_CAMPOS = 2.0  # por encima de los pixmaps de página (z = 1)


class FormLayer:
    def __init__(self, visor: ViewerWidget) -> None:
        self._visor = visor
        self._campos_por_pagina: dict[int, list[CampoFormulario]] = {}
        self._proxies: dict[str, QGraphicsProxyWidget] = {}

        visor.escena_reconstruida.connect(self._al_reconstruir_escena)
        visor.vista_actualizada.connect(self._sincronizar)

    def set_campos(self, campos: tuple[CampoFormulario, ...]) -> None:
        self._campos_por_pagina = {}
        for campo in campos:
            self._campos_por_pagina.setdefault(campo.pagina, []).append(campo)
        self._al_reconstruir_escena()  # descarta proxies previos
        self._sincronizar()

    def proxies(self) -> dict[str, QGraphicsProxyWidget]:
        return dict(self._proxies)

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
        proxy = escena.addWidget(widget)
        proxy.setZValue(_Z_CAMPOS)
        self._proxies[campo.id] = proxy
        self._posicionar(proxy, campo)

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
