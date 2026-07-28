"""Escritura de Rich Text Format (.rtf) desde la estructura de la página.

RTF es ASCII: todo lo que no lo sea va escapado como `\\uN?`, con el carácter de
sustitución detrás para los lectores que no entiendan Unicode. Las tablas se
escriben con el modelo de filas y celdas de RTF (`\\trowd`, `\\cellx`).
"""

from __future__ import annotations

import os
from pathlib import Path

from lectorpdf.adapters.pymupdf.estructura import Bloque

_CABECERA = r"{\rtf1\ansi\ansicpg1252\deff0{\fonttbl{\f0\fswiss Helvetica;}}" + "\n"
_ANCHO_TABLA_TWIPS = 9000  # ancho útil de un A4 con márgenes normales


def escribir_rtf(bloques: list[Bloque], destino: Path) -> None:
    """Escribe el .rtf de forma atómica (temporal + replace)."""
    tmp = destino.with_name(destino.name + ".tmp")
    partes = [_CABECERA]
    for bloque in bloques:
        if bloque.es_tabla:
            partes.append(_tabla(bloque))
        elif bloque.es_titulo:
            tam = {1: 32, 2: 28, 3: 24}.get(bloque.nivel, 24)  # medios puntos
            partes.append(
                rf"\pard\sb200\sa100\b\fs{tam} {_escapar(bloque.texto.strip())}"
                + "\\b0\\fs22\\par\n"
            )
        else:
            partes.append(r"\pard\sa100\fs22 " + _tramos(bloque) + "\\par\n")
    partes.append("}\n")
    tmp.write_text("".join(partes), encoding="ascii")
    os.replace(tmp, destino)


def _tramos(bloque: Bloque) -> str:
    partes: list[str] = []
    for tramo in bloque.tramos:
        texto = _escapar(tramo.texto)
        partes.append(rf"\b {texto}\b0 " if tramo.negrita else texto)
    return "".join(partes)


def _tabla(bloque: Bloque) -> str:
    columnas = max(len(fila) for fila in bloque.filas)
    ancho = _ANCHO_TABLA_TWIPS // max(columnas, 1)
    lineas: list[str] = []
    for fila in bloque.filas:
        lineas.append(r"\trowd\trgaph100")
        for c in range(columnas):
            lineas.append(rf"\cellx{ancho * (c + 1)}")
        lineas.append("\n")
        celdas = list(fila) + [""] * (columnas - len(fila))
        for celda in celdas:
            lineas.append(rf"\pard\intbl\fs22 {_escapar(celda)}\cell")
        lineas.append("\\row\n")
    lineas.append(r"\pard" + "\n")
    return "".join(lineas)


def _escapar(texto: str) -> str:
    salida: list[str] = []
    for caracter in texto:
        if caracter in "\\{}":
            salida.append("\\" + caracter)
        elif caracter == "\n":
            salida.append(r"\line ")
        elif ord(caracter) < 128:
            salida.append(caracter)
        else:
            # \uN necesita el código con signo y un sustituto ASCII detrás.
            punto = ord(caracter)
            if punto > 32767:
                punto -= 65536
            salida.append(rf"\u{punto}?")
    return "".join(salida)
