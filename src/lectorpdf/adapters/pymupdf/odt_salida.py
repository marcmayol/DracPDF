"""Escritura de OpenDocument Text (.odt) desde la estructura de la página.

El paquete ODF se escribe a mano (es un ZIP con XML dentro), sin dependencias:
`mimetype` primero y sin comprimir como exige la especificación, el manifiesto,
los estilos y el contenido.
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from lectorpdf.adapters.pymupdf.estructura import Bloque

_MIMETYPE = "application/vnd.oasis.opendocument.text"

_MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest
    xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
    manifest:version="1.3">
  <manifest:file-entry manifest:full-path="/" manifest:media-type="{mime}"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
</manifest:manifest>
"""

_STYLES = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
    xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
    office:version="1.3">
  <office:styles>
    <style:style style:name="Standard" style:family="paragraph"/>
  </office:styles>
</office:document-styles>
"""

_CABECERA_CONTENIDO = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
    xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
    xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
    office:version="1.3">
  <office:automatic-styles>
    <style:style style:name="Negrita" style:family="text">
      <style:text-properties fo:font-weight="bold"/>
    </style:style>
  </office:automatic-styles>
  <office:body>
    <office:text>
"""

_PIE_CONTENIDO = """    </office:text>
  </office:body>
</office:document-content>
"""


def escribir_odt(bloques: list[Bloque], destino: Path) -> None:
    """Escribe el .odt de forma atómica (temporal + replace)."""
    tmp = destino.with_name(destino.name + ".tmp")
    contenido = _CABECERA_CONTENIDO + _cuerpo(bloques) + _PIE_CONTENIDO
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as paquete:
        paquete.writestr(
            zipfile.ZipInfo("mimetype"), _MIMETYPE, compress_type=zipfile.ZIP_STORED
        )
        paquete.writestr("META-INF/manifest.xml", _MANIFEST.format(mime=_MIMETYPE))
        paquete.writestr("styles.xml", _STYLES)
        paquete.writestr("content.xml", contenido)
    os.replace(tmp, destino)


def _cuerpo(bloques: list[Bloque]) -> str:
    partes: list[str] = []
    for bloque in bloques:
        if bloque.es_tabla:
            partes.append(_tabla(bloque))
        elif bloque.es_titulo:
            partes.append(
                f'      <text:h text:outline-level="{bloque.nivel}">'
                f"{escape(bloque.texto.strip())}</text:h>\n"
            )
        else:
            partes.append(f"      <text:p>{_tramos(bloque)}</text:p>\n")
    return "".join(partes)


def _tramos(bloque: Bloque) -> str:
    partes: list[str] = []
    for tramo in bloque.tramos:
        texto = escape(tramo.texto)
        if tramo.negrita:
            partes.append(f'<text:span text:style-name="Negrita">{texto}</text:span>')
        else:
            partes.append(texto)
    return "".join(partes)


def _tabla(bloque: Bloque) -> str:
    columnas = max(len(fila) for fila in bloque.filas)
    lineas = ['      <table:table table:name="Tabla">\n']
    lineas.append(
        f'        <table:table-column table:number-columns-repeated="{columnas}"/>\n'
    )
    for fila in bloque.filas:
        lineas.append("        <table:table-row>\n")
        celdas = list(fila) + [""] * (columnas - len(fila))
        for celda in celdas:
            lineas.append(
                "          <table:table-cell office:value-type='string'>"
                f"<text:p>{escape(celda)}</text:p></table:table-cell>\n"
            )
        lineas.append("        </table:table-row>\n")
    lineas.append("      </table:table>\n")
    return "".join(lineas)
