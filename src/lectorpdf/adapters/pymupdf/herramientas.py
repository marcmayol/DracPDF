"""Adaptador de `ServicioHerramientas` sobre PyMuPDF.

Las operaciones sobre el documento abierto usan el `RegistroDocumentos`
compartido; las que lo MUTAN (rotar/eliminar/mover) rechazan si está FIRMADO.
Unir y desproteger trabajan sobre rutas de ficheros cerrados.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import fitz
from PIL import Image

from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.conversion import CALIDAD_POR_DEFECTO, FormatoImagen
from lectorpdf.core.domain.errores import (
    ContrasenaIncorrecta,
    DocumentoFirmado,
    RangoInvalido,
    SinPaginas,
)
from lectorpdf.core.domain.herramientas import Progreso, Rango, ResultadoCompresion
from lectorpdf.core.domain.modelos import Pagina


class PyMuPDFHerramientas:
    def __init__(self, registro: RegistroDocumentos) -> None:
        self._registro = registro

    # -- Rutas de ficheros cerrados -----------------------------------------

    def unir(
        self, rutas: Sequence[Path], destino: Path, progreso: Progreso | None = None
    ) -> None:
        if not rutas:
            raise SinPaginas("No hay ficheros que unir")
        salida = fitz.open()
        try:
            total = len(rutas)
            for i, ruta in enumerate(rutas):
                with fitz.open(ruta) as origen:
                    salida.insert_pdf(origen)
                if progreso is not None:
                    progreso(i + 1, total)  # puede lanzar OperacionCancelada
            salida.save(str(destino), garbage=3, deflate=True)
        finally:
            salida.close()

    def desproteger(self, ruta: Path, contrasena: str, destino: Path) -> None:
        doc = fitz.open(ruta)
        try:
            if doc.needs_pass and not doc.authenticate(contrasena):
                raise ContrasenaIncorrecta("Contraseña incorrecta")
            doc.save(str(destino), encryption=fitz.PDF_ENCRYPT_NONE)
        finally:
            doc.close()

    # -- Documento abierto: mutaciones (rechazan si FIRMADO) ----------------

    def rotar_pagina(
        self, documento_id: str, indice: int, grados: int
    ) -> tuple[Pagina, ...]:
        doc = self._doc_editable(documento_id)
        self._validar_indice(doc, indice)
        pagina = doc[indice]
        pagina.set_rotation((pagina.rotation + grados) % 360)
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)
        return _paginas(doc)

    def eliminar_pagina(
        self, documento_id: str, indice: int
    ) -> tuple[Pagina, ...]:
        doc = self._doc_editable(documento_id)
        self._validar_indice(doc, indice)
        if doc.page_count <= 1:
            raise SinPaginas("No se puede dejar el documento sin páginas")
        doc.delete_page(indice)
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)
        return _paginas(doc)

    def mover_pagina(
        self, documento_id: str, origen: int, destino: int
    ) -> tuple[Pagina, ...]:
        doc = self._doc_editable(documento_id)
        self._validar_indice(doc, origen)
        self._validar_indice(doc, destino)
        orden = list(range(doc.page_count))
        orden.insert(destino, orden.pop(origen))
        doc.select(orden)
        self._registro.marcar(documento_id, Marca.CAMBIOS_SIN_GUARDAR)
        return _paginas(doc)

    # -- Documento abierto: derivan a fichero nuevo -------------------------

    def dividir(
        self, documento_id: str, rangos: Sequence[Rango], directorio: Path
    ) -> list[Path]:
        doc = self._registro.obtener(documento_id)
        base = Path(doc.name).stem or "documento"
        directorio.mkdir(parents=True, exist_ok=True)
        rutas: list[Path] = []
        for rango in rangos:
            if rango.inicio < 1 or rango.fin > doc.page_count:
                raise RangoInvalido(
                    f"Rango {rango.inicio}-{rango.fin} fuera de [1, {doc.page_count}]"
                )
            parte = fitz.open()
            try:
                parte.insert_pdf(doc, from_page=rango.inicio - 1, to_page=rango.fin - 1)
                salida = directorio / f"{base}_{rango.inicio}-{rango.fin}.pdf"
                parte.save(str(salida), garbage=3, deflate=True)
            finally:
                parte.close()
            rutas.append(salida)
        return rutas

    def proteger(self, documento_id: str, destino: Path, contrasena: str) -> None:
        doc = self._registro.obtener(documento_id)
        doc.save(
            str(destino),
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw=contrasena,
            user_pw=contrasena,
        )

    def comprimir(
        self, documento_id: str, destino: Path, progreso: Progreso | None = None
    ) -> ResultadoCompresion:
        doc = self._registro.obtener(documento_id)
        origen = Path(doc.name)
        bytes_antes = origen.stat().st_size if origen.is_file() else len(doc.tobytes())
        if progreso is not None:
            progreso(0, 1)
        doc.save(str(destino), garbage=4, deflate=True, clean=True)
        if progreso is not None:
            progreso(1, 1)
        return ResultadoCompresion(bytes_antes, destino.stat().st_size)

    def exportar_imagenes(
        self,
        documento_id: str,
        directorio: Path,
        dpi: int,
        formato: FormatoImagen = FormatoImagen.PNG,
        calidad: int = CALIDAD_POR_DEFECTO,
        progreso: Progreso | None = None,
    ) -> list[Path]:
        doc = self._registro.obtener(documento_id)
        base = Path(doc.name).stem or "documento"
        directorio.mkdir(parents=True, exist_ok=True)
        total = doc.page_count

        if formato.es_vectorial:
            return self._exportar_svg(doc, directorio, base, total, progreso)
        if formato.es_multipagina:
            return self._exportar_tiff(doc, directorio, base, dpi, total, progreso)

        rutas: list[Path] = []
        for i in range(total):
            pix = doc[i].get_pixmap(dpi=dpi)
            salida = directorio / f"{base}_p{i + 1}{formato.extension}"
            _escribir_imagen(pix, salida, formato, calidad)
            rutas.append(salida)
            if progreso is not None:
                progreso(i + 1, total)
        return rutas

    def _exportar_svg(
        self,
        doc: fitz.Document,
        directorio: Path,
        base: str,
        total: int,
        progreso: Progreso | None,
    ) -> list[Path]:
        rutas: list[Path] = []
        for i in range(total):
            salida = directorio / f"{base}_p{i + 1}.svg"
            # text_as_path=False deja el texto como texto (editable en Inkscape o
            # Illustrator); por omisión MuPDF lo convertiría en trazos.
            salida.write_text(
                doc[i].get_svg_image(text_as_path=False), encoding="utf-8"
            )
            rutas.append(salida)
            if progreso is not None:
                progreso(i + 1, total)
        return rutas

    def _exportar_tiff(
        self,
        doc: fitz.Document,
        directorio: Path,
        base: str,
        dpi: int,
        total: int,
        progreso: Progreso | None,
    ) -> list[Path]:
        """Todas las páginas en un único TIFF, que es lo que lo hace útil."""
        paginas: list[Image.Image] = []
        for i in range(total):
            paginas.append(_a_pillow(doc[i].get_pixmap(dpi=dpi)))
            if progreso is not None:
                progreso(i + 1, total)
        salida = directorio / f"{base}.tiff"
        if not paginas:
            raise SinPaginas("El documento no tiene páginas que convertir")
        paginas[0].save(
            str(salida), save_all=True, append_images=paginas[1:], compression="tiff_lzw"
        )
        return [salida]

    def exportar_texto(self, documento_id: str, destino: Path) -> None:
        doc = self._registro.obtener(documento_id)
        texto = "\n".join(doc[i].get_text() for i in range(doc.page_count))
        destino.write_text(texto, encoding="utf-8")

    # -- Interno ------------------------------------------------------------

    def _doc_editable(self, documento_id: str) -> fitz.Document:
        if self._registro.tiene(documento_id, Marca.FIRMADO):
            raise DocumentoFirmado(
                "El documento está firmado: no se pueden reorganizar sus páginas"
            )
        return self._registro.obtener(documento_id)

    @staticmethod
    def _validar_indice(doc: fitz.Document, indice: int) -> None:
        if indice < 0 or indice >= doc.page_count:
            raise RangoInvalido(f"Página {indice} fuera de [0, {doc.page_count})")


def _a_pillow(pix: fitz.Pixmap) -> Image.Image:
    """Convierte el pixmap de MuPDF (RGB, sin alfa) a una imagen de Pillow."""
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def _escribir_imagen(
    pix: fitz.Pixmap, salida: Path, formato: FormatoImagen, calidad: int
) -> None:
    """PNG y JPEG los escribe MuPDF; WEBP necesita Pillow."""
    if formato is FormatoImagen.PNG:
        pix.save(str(salida))
        return
    if formato is FormatoImagen.JPEG:
        salida.write_bytes(pix.tobytes("jpg", jpg_quality=calidad))
        return
    _a_pillow(pix).save(str(salida), quality=calidad)


def _paginas(doc: fitz.Document) -> tuple[Pagina, ...]:
    return tuple(
        Pagina(indice=i, ancho_pt=doc[i].rect.width, alto_pt=doc[i].rect.height)
        for i in range(doc.page_count)
    )
