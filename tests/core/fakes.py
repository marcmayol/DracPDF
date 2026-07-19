"""Fakes de los puertos para testear casos de uso sin infraestructura."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.errores import CampoNoEncontrado, DocumentoNoAbierto
from lectorpdf.core.domain.formularios import CampoFormulario, RectanguloPt
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


class FakeFormService:
    """Fake en memoria de `FormService`. Registra escrituras y guardados."""

    def __init__(
        self,
        campos: tuple[CampoFormulario, ...] = (),
        es_xfa: bool = False,
    ) -> None:
        self._campos = campos
        self._es_xfa = es_xfa
        self.escrituras: list[tuple[str, str, str]] = []
        self.guardados: list[tuple[str, Path | None]] = []
        self.sucio = False

    def es_xfa(self, documento_id: str) -> bool:
        return self._es_xfa

    def listar_campos(self, documento_id: str) -> tuple[CampoFormulario, ...]:
        return self._campos

    def escribir_valor(self, documento_id: str, campo_id: str, valor: str) -> None:
        if all(c.id != campo_id for c in self._campos):
            raise CampoNoEncontrado(campo_id)
        self.escrituras.append((documento_id, campo_id, valor))
        self.sucio = True

    def esta_sucio(self, documento_id: str) -> bool:
        return self.sucio

    def guardar_incremental(self, documento_id: str, destino: Path | None) -> None:
        self.guardados.append((documento_id, destino))
        self.sucio = False


class FakeEstampadoService:
    """Fake en memoria de `EstampadoService`. Registra los estampados."""

    def __init__(self) -> None:
        self.estampados: list[tuple[str, int, RectanguloPt, bytes]] = []

    def estampar_imagen(
        self,
        documento_id: str,
        pagina: int,
        rect_pt: RectanguloPt,
        imagen_png: bytes,
    ) -> None:
        self.estampados.append((documento_id, pagina, rect_pt, imagen_png))
