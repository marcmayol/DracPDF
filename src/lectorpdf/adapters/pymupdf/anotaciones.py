"""Adaptador de `ServicioAnotaciones` sobre PyMuPDF (Fase 9).

Comparte el `RegistroDocumentos`. El texto nuevo se hornea con `insert_textbox` y
una fuente OFL embebida (`insert_font`), de modo que el PDF resultante embebe la
fuente (Type0) y se ve igual en cualquier máquina. Cada operación de contenido se
registra en el historial de contenido para deshacer/rehacer: deshacer restaura el
content stream de la página (descartando lo añadido); rehacer re-ejecuta la
operación.
"""

from __future__ import annotations

import fitz

from lectorpdf.adapters.pymupdf.fuentes import nombre_fuente, ruta_fuente
from lectorpdf.adapters.pymupdf.historial_contenido import OperacionContenido
from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.anotaciones import TextoNuevo
from lectorpdf.core.domain.errores import DocumentoFirmado, PaginaFueraDeRango

# Snapshot mínimo del contenido de una página: (xref del content stream, bytes).
_Snapshot = tuple[int, bytes]


class PyMuPDFAnotaciones:
    def __init__(self, registro: RegistroDocumentos) -> None:
        self._registro = registro

    # -- Texto --------------------------------------------------------------

    def anadir_texto(
        self, documento_id: str, pagina: int, texto: TextoNuevo
    ) -> None:
        self._exigir_editable(documento_id)
        doc = self._registro.obtener(documento_id)
        self._exigir_pagina(doc, pagina)

        antes = _snapshot(doc[pagina])
        self._escribir_texto(doc[pagina], texto)

        def deshacer() -> None:
            _restaurar(self._registro.obtener(documento_id)[pagina], antes)

        def rehacer() -> None:
            self._escribir_texto(self._registro.obtener(documento_id)[pagina], texto)

        self._registro.historial_contenido(documento_id).registrar(
            OperacionContenido((pagina,), deshacer, rehacer)
        )
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)

    def _escribir_texto(self, page: fitz.Page, texto: TextoNuevo) -> None:
        nombre = nombre_fuente(texto.fuente)
        page.insert_font(fontname=nombre, fontfile=ruta_fuente(texto.fuente))
        rect = fitz.Rect(
            texto.rect_pt.x0, texto.rect_pt.y0, texto.rect_pt.x1, texto.rect_pt.y1
        )
        page.insert_textbox(
            rect,
            texto.texto,
            fontname=nombre,
            fontsize=texto.tamano,
            color=texto.color,
        )

    # -- Deshacer / rehacer de contenido ------------------------------------

    def puede_deshacer(self, documento_id: str) -> bool:
        return self._registro.historial_contenido(documento_id).puede_deshacer()

    def puede_rehacer(self, documento_id: str) -> bool:
        return self._registro.historial_contenido(documento_id).puede_rehacer()

    def deshacer(self, documento_id: str) -> tuple[int, ...] | None:
        operacion = self._registro.historial_contenido(documento_id).deshacer()
        if operacion is None:
            return None
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)
        return operacion.paginas

    def rehacer(self, documento_id: str) -> tuple[int, ...] | None:
        operacion = self._registro.historial_contenido(documento_id).rehacer()
        if operacion is None:
            return None
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)
        return operacion.paginas

    # -- Ayudas -------------------------------------------------------------

    def _exigir_editable(self, documento_id: str) -> None:
        if self._registro.tiene(documento_id, Marca.FIRMADO):
            raise DocumentoFirmado(
                "El documento está firmado: la edición está bloqueada"
            )

    def _exigir_pagina(self, doc: fitz.Document, pagina: int) -> None:
        if pagina < 0 or pagina >= doc.page_count:
            raise PaginaFueraDeRango(
                f"Página {pagina} fuera de rango [0, {doc.page_count})"
            )


def _snapshot(page: fitz.Page) -> _Snapshot:
    """Consolida el contenido de la página en un solo stream y lo captura."""
    page.clean_contents()
    xref = page.get_contents()[0]
    return xref, page.parent.xref_stream(xref)


def _restaurar(page: fitz.Page, snapshot: _Snapshot) -> None:
    """Devuelve la página al estado del snapshot: restaura el stream original y
    deja /Contents apuntando solo a él (descarta cualquier stream añadido)."""
    xref, datos = snapshot
    page.parent.update_stream(xref, datos)
    page.set_contents(xref)
