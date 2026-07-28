"""Adaptador de `ConversorImagenes` con PyMuPDF (imágenes → PDF).

Una imagen por página, en el orden recibido. Con `TAMANO_IMAGEN` cada página
adopta el tamaño de su imagen (MuPDF la envuelve en un PDF de una página);
con `PAGINA_FIJA` todas las páginas miden lo que diga `ConfigPagina` y la
imagen se escala dentro de los márgenes conservando su proporción.

Escritura atómica (temporal + replace), como todo lo que escribe fichero.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

import fitz

from lectorpdf.core.domain.conversion import AjusteImagen, ConfigPagina
from lectorpdf.core.domain.errores import ErrorDominio
from lectorpdf.core.domain.herramientas import Progreso

_MM_A_PT = 72.0 / 25.4


class ConversorImagenesFitz:
    def a_pdf(
        self,
        rutas: Sequence[Path],
        destino: Path,
        ajuste: AjusteImagen,
        config: ConfigPagina,
        progreso: Progreso | None = None,
    ) -> None:
        tmp = destino.with_name(destino.name + ".tmp")
        salida = fitz.open()
        try:
            total = len(rutas)
            for indice, ruta in enumerate(rutas):
                self._anadir_pagina(salida, ruta, ajuste, config)
                if progreso is not None:
                    progreso(indice + 1, total)
            salida.save(str(tmp))
        finally:
            salida.close()
        os.replace(tmp, destino)  # solo si el guardado no lanzó

    def _anadir_pagina(
        self,
        salida: fitz.Document,
        ruta: Path,
        ajuste: AjusteImagen,
        config: ConfigPagina,
    ) -> None:
        if ajuste is AjusteImagen.PAGINA_FIJA:
            ancho = config.ancho_mm * _MM_A_PT
            alto = config.alto_mm * _MM_A_PT
            margen = config.margen_mm * _MM_A_PT
            marco = fitz.Rect(margen, margen, ancho - margen, alto - margen)
            if marco.is_empty or marco.width <= 0 or marco.height <= 0:
                raise ErrorDominio("Los márgenes no dejan espacio para la imagen")
            pagina = salida.new_page(width=ancho, height=alto)
            try:
                pagina.insert_image(marco, filename=str(ruta), keep_proportion=True)
            except ErrorDominio:
                raise
            except Exception as exc:  # noqa: BLE001 - el motor no distingue causas
                raise ErrorDominio(f"No se pudo leer la imagen: {ruta.name}") from exc
            return

        # El formato solo se valida de verdad al cargar la página, no al abrir:
        # un fichero con extensión de imagen y contenido basura falla aquí.
        try:
            imagen = fitz.open(str(ruta))
            try:
                if imagen.is_pdf:  # un .png que en realidad era otra cosa
                    raise ErrorDominio(f"No es una imagen: {ruta.name}")
                pdf = fitz.open("pdf", imagen.convert_to_pdf())
                try:
                    salida.insert_pdf(pdf)
                finally:
                    pdf.close()
            finally:
                imagen.close()
        except ErrorDominio:
            raise
        except Exception as exc:  # noqa: BLE001 - el motor no distingue causas
            raise ErrorDominio(f"No se pudo leer la imagen: {ruta.name}") from exc
