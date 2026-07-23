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
from lectorpdf.core.domain.anotaciones import (
    Color,
    Correccion,
    FuenteTexto,
    Nota,
    TextoNuevo,
    TipoMarcado,
)
from lectorpdf.core.domain.errores import (
    DocumentoFirmado,
    PaginaFueraDeRango,
    TextoNoCabe,
)
from lectorpdf.core.domain.formularios import RectanguloPt

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

    # -- Marcado sobre selección (anotaciones estándar) ---------------------

    def marcar(
        self,
        documento_id: str,
        pagina: int,
        rects_pt: tuple[RectanguloPt, ...],
        tipo: TipoMarcado,
        color: Color,
    ) -> None:
        self._exigir_editable(documento_id)
        doc = self._registro.obtener(documento_id)
        self._exigir_pagina(doc, pagina)

        ref = [self._crear_marcado(doc[pagina], rects_pt, tipo, color)]

        def deshacer() -> None:
            _eliminar_por_xref(self._registro.obtener(documento_id)[pagina], ref[0])

        def rehacer() -> None:
            ref[0] = self._crear_marcado(
                self._registro.obtener(documento_id)[pagina], rects_pt, tipo, color
            )

        self._registro.historial_contenido(documento_id).registrar(
            OperacionContenido((pagina,), deshacer, rehacer)
        )
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)

    def _crear_marcado(
        self,
        page: fitz.Page,
        rects_pt: tuple[RectanguloPt, ...],
        tipo: TipoMarcado,
        color: Color,
    ) -> int:
        rects = [fitz.Rect(r.x0, r.y0, r.x1, r.y1) for r in rects_pt]
        if tipo is TipoMarcado.RESALTADO:
            annot = page.add_highlight_annot(rects)
        elif tipo is TipoMarcado.SUBRAYADO:
            annot = page.add_underline_annot(rects)
        else:
            annot = page.add_strikeout_annot(rects)
        annot.set_colors(stroke=color)
        annot.update()
        return int(annot.xref)

    def anadir_nota(self, documento_id: str, pagina: int, nota: Nota) -> None:
        self._exigir_editable(documento_id)
        doc = self._registro.obtener(documento_id)
        self._exigir_pagina(doc, pagina)

        ref = [self._crear_nota(doc[pagina], nota)]

        def deshacer() -> None:
            _eliminar_por_xref(self._registro.obtener(documento_id)[pagina], ref[0])

        def rehacer() -> None:
            ref[0] = self._crear_nota(self._registro.obtener(documento_id)[pagina], nota)

        self._registro.historial_contenido(documento_id).registrar(
            OperacionContenido((pagina,), deshacer, rehacer)
        )
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)

    def _crear_nota(self, page: fitz.Page, nota: Nota) -> int:
        annot = page.add_text_annot(fitz.Point(nota.x_pt, nota.y_pt), nota.texto)
        annot.update()
        return int(annot.xref)

    def anotacion_en(
        self, documento_id: str, pagina: int, x_pt: float, y_pt: float
    ) -> int | None:
        doc = self._registro.obtener(documento_id)
        self._exigir_pagina(doc, pagina)
        punto = fitz.Point(x_pt, y_pt)
        encontrada: int | None = None
        for annot in doc[pagina].annots():
            if annot.rect.contains(punto):
                encontrada = int(annot.xref)  # el último dibujado (arriba) gana
        return encontrada

    def eliminar_anotacion(
        self, documento_id: str, pagina: int, xref: int
    ) -> None:
        self._exigir_editable(documento_id)
        doc = self._registro.obtener(documento_id)
        self._exigir_pagina(doc, pagina)
        _eliminar_por_xref(doc[pagina], xref)
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)

    # -- Corrección de texto (Parte B) --------------------------------------

    def cabe_texto(
        self,
        documento_id: str,
        pagina: int,
        rect_pt: RectanguloPt,
        texto: str,
        fuente: FuenteTexto,
    ) -> bool:
        _font, _r, _tam, _ancho, cabe = _metricas(rect_pt, texto, fuente)
        return cabe

    def corregir_texto(
        self, documento_id: str, pagina: int, correccion: Correccion
    ) -> None:
        self._exigir_editable(documento_id)
        doc = self._registro.obtener(documento_id)
        self._exigir_pagina(doc, pagina)

        font, r, tam, ancho, cabe = _metricas(
            correccion.rect_pt, correccion.texto_nuevo, correccion.fuente
        )
        if not cabe:
            if not correccion.reducir:
                raise TextoNoCabe(
                    "El texto nuevo no cabe: reduce el tamaño o cancela"
                )
            tam = tam * r.width / ancho  # encoger para que quepa a lo ancho

        antes = _snapshot(doc[pagina])
        self._aplicar_correccion(doc[pagina], r, correccion, font, tam)

        def deshacer() -> None:
            _restaurar(self._registro.obtener(documento_id)[pagina], antes)

        def rehacer() -> None:
            self._aplicar_correccion(
                self._registro.obtener(documento_id)[pagina], r, correccion, font, tam
            )

        self._registro.historial_contenido(documento_id).registrar(
            OperacionContenido((pagina,), deshacer, rehacer)
        )
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)

    def _aplicar_correccion(
        self,
        page: fitz.Page,
        r: fitz.Rect,
        correccion: Correccion,
        font: fitz.Font,
        tam: float,
    ) -> None:
        page.add_redact_annot(r)
        page.apply_redactions()
        nombre = nombre_fuente(correccion.fuente)
        page.insert_font(fontname=nombre, fontfile=ruta_fuente(correccion.fuente))
        baseline = fitz.Point(r.x0, r.y1 + font.descender * tam)
        page.insert_text(
            baseline,
            correccion.texto_nuevo,
            fontname=nombre,
            fontsize=tam,
            color=correccion.color,
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


def _eliminar_por_xref(page: fitz.Page, xref: int) -> None:
    for annot in page.annots():
        if annot.xref == xref:
            page.delete_annot(annot)
            return


def _metricas(
    rect_pt: RectanguloPt, texto: str, fuente: FuenteTexto
) -> tuple[fitz.Font, fitz.Rect, float, float, bool]:
    """(fuente, rect, tamaño que casa la altura, ancho del nuevo, ¿cabe a lo ancho?)."""
    font = fitz.Font(fontfile=ruta_fuente(fuente))
    r = fitz.Rect(rect_pt.x0, rect_pt.y0, rect_pt.x1, rect_pt.y1)
    alto_em = font.ascender - font.descender
    tam = r.height / alto_em if alto_em else 12.0
    ancho = font.text_length(texto, fontsize=tam)
    cabe = ancho <= r.width + 0.5
    return font, r, tam, ancho, cabe
