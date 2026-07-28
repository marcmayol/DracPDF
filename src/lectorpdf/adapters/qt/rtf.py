"""Lectura de Rich Text Format (.rtf) a HTML.

RTF es texto ASCII con marcas: grupos entre llaves, control words `\\palabra` y
caracteres escapados. No hay librería pura de referencia, así que se lee con un
parser propio deliberadamente acotado, y se traduce a HTML para reutilizar el
paginado de la cadena Qt.

Alcance declarado ("reformateado"): párrafos, saltos de línea, negrita, cursiva,
subrayado y caracteres no ASCII (`\\uN` y `\\'hh`). Las control words que no se
entienden se ignoran, y los grupos marcados como ignorables (`\\*`), junto con
las tablas de fuentes, colores y la información del documento, se descartan
enteros para que su contenido no acabe impreso como texto.
"""

from __future__ import annotations

import re
from html import escape
from pathlib import Path

#: Grupos cuyo contenido no es texto del documento.
_GRUPOS_DESCARTABLES = frozenset(
    {"fonttbl", "colortbl", "stylesheet", "info", "pict", "header", "footer"}
)

_MARCAS = {"b": "b", "i": "i", "ul": "u"}

_TOKEN = re.compile(
    r"""
    (?P<grupo_ini>\{)
  | (?P<grupo_fin>\})
  | \\(?P<hex>'[0-9a-fA-F]{2})
  | \\(?P<escapado>[\\{}])
  | \\(?P<palabra>[a-zA-Z]+)(?P<parametro>-?\d+)?[ ]?
  | \\(?P<simbolo>[^a-zA-Z])
  | (?P<texto>[^\\{}]+)
    """,
    re.VERBOSE,
)


class _Estado:
    """Formato activo; se apila y desapila con los grupos, como manda RTF."""

    def __init__(self, marcas: frozenset[str] = frozenset()) -> None:
        self.marcas = marcas
        self.descartar = False
        self.codificacion = "cp1252"

    def copia(self) -> _Estado:
        nuevo = _Estado(self.marcas)
        nuevo.descartar = self.descartar
        nuevo.codificacion = self.codificacion
        return nuevo


def rtf_a_html(ruta: Path) -> str:
    """Traduce el .rtf a un HTML que la cadena Qt sabe paginar."""
    datos = ruta.read_bytes()
    if not datos.lstrip().startswith(b"{\\rtf"):
        raise ValueError(f"No es un documento RTF válido: {ruta.name}")
    return _convertir(datos.decode("latin-1"))


def _convertir(bruto: str) -> str:
    pila: list[_Estado] = [_Estado()]
    parrafos: list[list[str]] = [[]]
    saltar_unicode = 0

    for token in _TOKEN.finditer(bruto):
        estado = pila[-1]
        if token["grupo_ini"] is not None:
            pila.append(estado.copia())
            continue
        if token["grupo_fin"] is not None:
            if len(pila) > 1:
                pila.pop()
            continue

        if token["simbolo"] is not None:
            if token["simbolo"] == "*":
                estado.descartar = True  # grupo ignorable: \*\algo
            continue

        if token["palabra"] is not None:
            palabra = token["palabra"]
            parametro = token["parametro"]
            if palabra in _GRUPOS_DESCARTABLES:
                estado.descartar = True
                continue
            if palabra == "par":
                parrafos.append([])
                continue
            if palabra == "line":
                if not estado.descartar:
                    parrafos[-1].append("<br>")
                continue
            if palabra in _MARCAS:
                if parametro == "0":
                    estado.marcas -= {palabra}
                else:
                    estado.marcas |= {palabra}
                continue
            if palabra == "plain":
                estado.marcas = frozenset()
                continue
            if palabra == "u" and parametro is not None:
                if not estado.descartar:
                    punto = int(parametro)
                    if punto < 0:
                        punto += 65536  # RTF firma los códigos por encima de 32767
                    parrafos[-1].append(
                        _con_marcas(escape(chr(punto)), estado.marcas)
                    )
                saltar_unicode = 1  # el carácter de reemplazo que sigue
                continue
            if palabra == "uc" and parametro is not None:
                saltar_unicode = 0
                continue
            continue  # control word no soportada: se ignora

        if token["hex"] is not None:
            if saltar_unicode:
                saltar_unicode -= 1
                continue
            if not estado.descartar:
                caracter = bytes.fromhex(token["hex"][1:]).decode(
                    estado.codificacion, errors="replace"
                )
                parrafos[-1].append(_con_marcas(escape(caracter), estado.marcas))
            continue

        texto = token["escapado"] or token["texto"]
        if texto is None or estado.descartar:
            continue
        texto = texto.replace("\r", "").replace("\n", "")
        if saltar_unicode:
            texto = texto[saltar_unicode:]
            saltar_unicode = 0
        if texto:
            parrafos[-1].append(_con_marcas(escape(texto), estado.marcas))

    cuerpo = "".join(
        f"<p>{''.join(partes)}</p>" for partes in parrafos if "".join(partes).strip()
    )
    return f"<html><body>{cuerpo}</body></html>"


def _con_marcas(texto: str, marcas: frozenset[str]) -> str:
    for clave in ("ul", "i", "b"):  # anidado estable
        if clave in marcas:
            etiqueta = _MARCAS[clave]
            texto = f"<{etiqueta}>{texto}</{etiqueta}>"
    return texto
