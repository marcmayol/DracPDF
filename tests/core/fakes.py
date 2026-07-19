"""Fakes de los puertos para testear casos de uso sin infraestructura."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.errores import DocumentoNoAbierto
from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada


class FakeDocumentRepository:
    """Fake en memoria de `DocumentRepository`. Registra las llamadas recibidas."""

    def __init__(
        self,
        documento: Documento | None = None,
        imagen: ImagenRenderizada | None = None,
    ) -> None:
        self._documento = documento
        self._imagen = imagen or ImagenRenderizada(
            ancho_px=1, alto_px=1, datos=b"\x00\x00\x00\x00", escala=1.0
        )
        self.abrir_llamado_con: Path | None = None
        self.render_llamado_con: tuple[str, int, float] | None = None
        self.render_llamadas: list[tuple[str, int, float]] = []
        self.cerrado: list[str] = []

    def abrir(self, ruta: Path) -> Documento:
        self.abrir_llamado_con = ruta
        if self._documento is None:
            raise AssertionError("El fake no tiene un documento configurado")
        return self._documento

    def renderizar_pagina(
        self, documento_id: str, indice: int, escala: float
    ) -> ImagenRenderizada:
        if self._documento is not None and documento_id != self._documento.id:
            raise DocumentoNoAbierto(documento_id)
        self.render_llamado_con = (documento_id, indice, escala)
        self.render_llamadas.append((documento_id, indice, escala))
        return self._imagen

    def cerrar(self, documento_id: str) -> None:
        self.cerrado.append(documento_id)
