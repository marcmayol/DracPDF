"""Adaptador de `FormService` sobre PyMuPDF.

Comparte el `RegistroDocumentos` con el repositorio de render, de modo que opera
sobre el mismo `fitz.Document` sin conocer al resto de adaptadores.
"""

from __future__ import annotations

from pathlib import Path

import fitz

from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.errores import CampoNoEncontrado, DocumentoFirmado
from lectorpdf.core.domain.formularios import (
    CampoFormulario,
    RectanguloPt,
    TipoCampo,
)

_TIPOS: dict[int, TipoCampo] = {
    fitz.PDF_WIDGET_TYPE_TEXT: TipoCampo.TEXTO,
    fitz.PDF_WIDGET_TYPE_CHECKBOX: TipoCampo.CASILLA,
    fitz.PDF_WIDGET_TYPE_RADIOBUTTON: TipoCampo.RADIO,
    fitz.PDF_WIDGET_TYPE_COMBOBOX: TipoCampo.COMBO,
    fitz.PDF_WIDGET_TYPE_LISTBOX: TipoCampo.LISTA,
}


class PyMuPDFFormService:
    """Implementa `FormService` con PyMuPDF."""

    def __init__(self, registro: RegistroDocumentos) -> None:
        self._registro = registro
        # PyMuPDF no limpia doc.is_dirty tras un guardado incremental (queda
        # True), así que el estado "sin guardar" se rastrea con marcas propias en
        # el registro compartido (así lo comparten formularios y estampado).

    def es_xfa(self, documento_id: str) -> bool:
        doc = self._registro.obtener(documento_id)
        try:
            tipo, _ = doc.xref_get_key(doc.pdf_catalog(), "AcroForm/XFA")
        except ValueError:
            return False
        return bool(tipo != "null")

    def listar_campos(self, documento_id: str) -> tuple[CampoFormulario, ...]:
        doc = self._registro.obtener(documento_id)
        campos: list[CampoFormulario] = []
        for pno in range(doc.page_count):
            for idx, widget in enumerate(doc[pno].widgets()):
                tipo = _TIPOS.get(widget.field_type)
                if tipo is None:
                    continue  # firma, botón de acción, etc.: no editables aquí
                campos.append(_a_campo(widget, pno, idx, tipo))
        return tuple(campos)

    def escribir_valor(self, documento_id: str, campo_id: str, valor: str) -> None:
        if self._registro.tiene(documento_id, Marca.FIRMADO):
            raise DocumentoFirmado("El documento está firmado: no se puede editar")
        doc = self._registro.obtener(documento_id)
        pagina, indice = _partir_id(campo_id)
        if pagina < 0 or pagina >= doc.page_count:
            raise CampoNoEncontrado(campo_id)
        for i, widget in enumerate(doc[pagina].widgets()):
            if i == indice:
                widget.field_value = valor
                widget.update()  # regenera la apariencia del campo en el PDF
                self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)
                return
        raise CampoNoEncontrado(campo_id)

    def esta_sucio(self, documento_id: str) -> bool:
        return self._registro.tiene(documento_id, Marca.CAMBIOS_SIN_GUARDAR)

    def guardar_incremental(self, documento_id: str, destino: Path | None) -> None:
        self._registro.guardar_incremental(documento_id, destino)


def _partir_id(campo_id: str) -> tuple[int, int]:
    try:
        pagina_txt, indice_txt = campo_id.split(":", 1)
        return int(pagina_txt), int(indice_txt)
    except ValueError as exc:
        raise CampoNoEncontrado(campo_id) from exc


def _a_campo(
    widget: fitz.Widget, pagina: int, indice: int, tipo: TipoCampo
) -> CampoFormulario:
    on_states = _estados_on(widget)
    return CampoFormulario(
        id=f"{pagina}:{indice}",
        nombre=widget.field_name or "",
        tipo=tipo,
        pagina=pagina,
        rect_pt=RectanguloPt(
            widget.rect.x0, widget.rect.y0, widget.rect.x1, widget.rect.y1
        ),
        valor=_valor_texto(widget.field_value),
        opciones=_opciones(widget, tipo, on_states),
        estado_activado=on_states[0] if on_states else None,
        solo_lectura=bool(widget.field_flags & fitz.PDF_FIELD_IS_READ_ONLY),
    )


def _valor_texto(valor: object) -> str:
    if valor is None or valor is False:
        return ""
    return str(valor)


def _estados_on(widget: fitz.Widget) -> tuple[str, ...]:
    estados = widget.button_states()
    if not estados:
        return ()
    normales = estados.get("normal") or []
    return tuple(s for s in normales if s != "Off")


def _opciones(
    widget: fitz.Widget, tipo: TipoCampo, on_states: tuple[str, ...]
) -> tuple[str, ...]:
    if tipo in (TipoCampo.COMBO, TipoCampo.LISTA):
        valores = widget.choice_values or []
        return tuple(_opcion_texto(v) for v in valores)
    if tipo in (TipoCampo.CASILLA, TipoCampo.RADIO):
        return on_states
    return ()


def _opcion_texto(opcion: object) -> str:
    # PyMuPDF puede dar cada opción como cadena o como [export, display].
    if isinstance(opcion, list | tuple) and opcion:
        return str(opcion[0])
    return str(opcion)
