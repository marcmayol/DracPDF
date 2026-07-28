"""Lectura de OpenDocument Text (.odt) a HTML.

Un .odt es un ZIP con `content.xml` (más `styles.xml` y las imágenes en
`Pictures/`). Se traduce a HTML porque la cadena Qt ya sabe componer HTML: así
ODT reutiliza el mismo paginado que Word, Markdown y HTML.

Alcance declarado ("reformateado"): párrafos, títulos, negrita/cursiva/subrayado,
listas, tablas simples e imágenes embebidas. No se interpretan estilos de página,
columnas, notas al pie ni objetos incrustados.
"""

from __future__ import annotations

import base64
import contextlib
import mimetypes
import zipfile
from html import escape
from pathlib import Path

from lxml import etree

_NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
}


def _etiqueta(elemento: etree._Element) -> tuple[str, str]:
    """Devuelve (prefijo, nombre local) de la etiqueta del elemento."""
    bruta = str(elemento.tag)
    if not bruta.startswith("{"):
        return "", bruta
    uri, _, local = bruta[1:].partition("}")
    for prefijo, valor in _NS.items():
        if valor == uri:
            return prefijo, local
    return "", local


class _Estilos:
    """Estilos de texto declarados en el documento, resueltos a HTML.

    ODT no marca la negrita en el texto: la pone en un estilo con nombre al que
    el tramo se refiere. Sin resolverlos, todo saldría en redonda.
    """

    def __init__(self) -> None:
        self._por_nombre: dict[str, set[str]] = {}

    def cargar(self, raiz: etree._Element) -> None:
        for estilo in raiz.iter(f"{{{_NS['style']}}}style"):
            nombre = estilo.get(f"{{{_NS['style']}}}name")
            if not nombre:
                continue
            marcas: set[str] = set()
            for props in estilo.iter(f"{{{_NS['style']}}}text-properties"):
                if props.get(f"{{{_NS['fo']}}}font-weight") == "bold":
                    marcas.add("b")
                if props.get(f"{{{_NS['fo']}}}font-style") == "italic":
                    marcas.add("i")
                if props.get(f"{{{_NS['style']}}}text-underline-style") not in (
                    None,
                    "none",
                ):
                    marcas.add("u")
            padre = estilo.get(f"{{{_NS['style']}}}parent-style-name")
            if padre and padre in self._por_nombre:
                marcas |= self._por_nombre[padre]
            self._por_nombre[nombre] = marcas

    def marcas(self, nombre: str | None) -> set[str]:
        return self._por_nombre.get(nombre or "", set())


class _Imagenes:
    """Imágenes del paquete, servidas como data: URI para que Qt las pinte."""

    def __init__(self, zip_odt: zipfile.ZipFile) -> None:
        self._zip = zip_odt

    def data_uri(self, ruta: str) -> str | None:
        try:
            datos = self._zip.read(ruta)
        except KeyError:
            return None
        tipo = mimetypes.guess_type(ruta)[0] or "image/png"
        return f"data:{tipo};base64,{base64.b64encode(datos).decode('ascii')}"


def odt_a_html(ruta: Path) -> str:
    """Traduce el .odt a un HTML que la cadena Qt sabe paginar."""
    try:
        with zipfile.ZipFile(ruta) as paquete:
            contenido = paquete.read("content.xml")
            estilos = _Estilos()
            with contextlib.suppress(KeyError):  # styles.xml es opcional
                estilos.cargar(etree.fromstring(paquete.read("styles.xml")))
            raiz = etree.fromstring(contenido)
            estilos.cargar(raiz)  # los automáticos viven en content.xml
            imagenes = _Imagenes(paquete)
            cuerpo = raiz.find(f".//{{{_NS['office']}}}text")
            partes = (
                [_nodo_a_html(hijo, estilos, imagenes) for hijo in cuerpo]
                if cuerpo is not None
                else []
            )
    except zipfile.BadZipFile as exc:
        raise ValueError(f"No es un documento ODT válido: {ruta.name}") from exc
    except etree.XMLSyntaxError as exc:
        raise ValueError(f"El ODT tiene el contenido dañado: {ruta.name}") from exc
    return "<html><body>" + "".join(partes) + "</body></html>"


def _hijos_a_html(
    elemento: etree._Element, estilos: _Estilos, imagenes: _Imagenes
) -> str:
    partes: list[str] = []
    if elemento.text:
        partes.append(escape(elemento.text))
    for hijo in elemento:
        partes.append(_nodo_a_html(hijo, estilos, imagenes))
        if hijo.tail:
            partes.append(escape(hijo.tail))
    return "".join(partes)


def _nodo_a_html(
    elemento: etree._Element, estilos: _Estilos, imagenes: _Imagenes
) -> str:
    prefijo, nombre = _etiqueta(elemento)
    interior = _hijos_a_html(elemento, estilos, imagenes)

    if prefijo == "text":
        if nombre == "h":
            nivel = elemento.get(f"{{{_NS['text']}}}outline-level") or "1"
            nivel_html = min(max(int(nivel), 1), 6)
            return f"<h{nivel_html}>{interior}</h{nivel_html}>"
        if nombre == "p":
            return f"<p>{interior}</p>" if interior.strip() else "<p><br></p>"
        if nombre == "span":
            marcas = estilos.marcas(elemento.get(f"{{{_NS['text']}}}style-name"))
            if not marcas:
                return interior
            for marca in ("u", "i", "b"):
                if marca in marcas:
                    interior = f"<{marca}>{interior}</{marca}>"
            return interior
        if nombre == "list":
            return f"<ul>{interior}</ul>"
        if nombre == "list-item":
            return f"<li>{interior}</li>"
        if nombre == "line-break":
            return "<br>"
        if nombre == "tab":
            return "&nbsp;&nbsp;&nbsp;&nbsp;"
        if nombre == "s":
            return "&nbsp;"
        return interior

    if prefijo == "table":
        if nombre == "table":
            return f"<table border='1' cellspacing='0' cellpadding='4'>{interior}</table>"
        if nombre == "table-row":
            return f"<tr>{interior}</tr>"
        if nombre == "table-cell":
            return f"<td>{interior}</td>"
        return interior

    if prefijo == "draw" and nombre == "image":
        ruta = elemento.get(f"{{{_NS['xlink']}}}href") or ""
        uri = imagenes.data_uri(ruta.lstrip("./"))
        return f"<img src='{uri}'>" if uri else ""

    return interior
