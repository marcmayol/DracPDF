"""Genera el .odt de fixture (paquete ODF escrito a mano, sin dependencias).

Se ejecuta desde los tests o a mano:

    uv run python tests/adapters/generar_fixtures_odt.py
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import fitz

_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
    xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
    xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
    xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    office:version="1.3">
  <office:automatic-styles>
    <style:style style:name="Negrita" style:family="text">
      <style:text-properties fo:font-weight="bold"/>
    </style:style>
    <style:style style:name="Cursiva" style:family="text">
      <style:text-properties fo:font-style="italic"/>
    </style:style>
  </office:automatic-styles>
  <office:body>
    <office:text>
      <text:h text:outline-level="1">Informe de prueba</text:h>
      <text:p>Un parrafo con <text:span text:style-name="Negrita">texto en negrita</text:span>
        y <text:span text:style-name="Cursiva">texto en cursiva</text:span>.</text:p>
      <text:h text:outline-level="2">Apartado segundo</text:h>
      <text:list>
        <text:list-item><text:p>primer punto</text:p></text:list-item>
        <text:list-item><text:p>segundo punto</text:p></text:list-item>
      </text:list>
      <table:table table:name="Tabla1">
        <table:table-row>
          <table:table-cell><text:p>Concepto</text:p></table:table-cell>
          <table:table-cell><text:p>Importe</text:p></table:table-cell>
        </table:table-row>
        <table:table-row>
          <table:table-cell><text:p>Alquiler</text:p></table:table-cell>
          <table:table-cell><text:p>750 EUR</text:p></table:table-cell>
        </table:table-row>
      </table:table>
      <text:p>
        <draw:frame draw:name="Imagen1">
          <draw:image xlink:href="Pictures/imagen.png"/>
        </draw:frame>
      </text:p>
      <text:p>Caracteres con acentos: año, gestion, ñu.</text:p>
    </office:text>
  </office:body>
</office:document-content>
"""

_STYLES = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
    xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
    office:version="1.3">
  <office:styles/>
</office:document-styles>
"""

_MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest
    xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
    manifest:version="1.3">
  <manifest:file-entry manifest:full-path="/"
      manifest:media-type="application/vnd.oasis.opendocument.text"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="Pictures/imagen.png"
      manifest:media-type="image/png"/>
</manifest:manifest>
"""


def _png_de_prueba() -> bytes:
    doc = fitz.open()
    pagina = doc.new_page(width=120, height=60)
    pagina.draw_rect(fitz.Rect(0, 0, 120, 60), color=(0.84, 0.16, 0.16), fill=(1, 1, 1))
    datos: bytes = pagina.get_pixmap(dpi=72).tobytes("png")
    doc.close()
    return datos


def generar_odt_prueba(destino: Path) -> Path:
    """ODT con título, párrafos con negrita y cursiva, lista, tabla e imagen."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as paquete:
        # El mimetype va primero y sin comprimir: lo exige la especificación ODF.
        paquete.writestr(
            zipfile.ZipInfo("mimetype"),
            "application/vnd.oasis.opendocument.text",
            compress_type=zipfile.ZIP_STORED,
        )
        paquete.writestr("META-INF/manifest.xml", _MANIFEST)
        paquete.writestr("content.xml", _CONTENT)
        paquete.writestr("styles.xml", _STYLES)
        paquete.writestr("Pictures/imagen.png", _png_de_prueba())
    return destino


if __name__ == "__main__":
    ruta = generar_odt_prueba(Path(__file__).parent / "fixtures" / "prueba.odt")
    print(f"Generado: {ruta}")
