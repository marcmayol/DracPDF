"""Estructura intermedia de una página: párrafos, títulos y tablas.

Un PDF no guarda "esto es un título": guarda texto con un tamaño y una posición.
Aquí se deduce una vez —el tamaño de fuente más frecuente es el cuerpo, lo
notablemente mayor es un título— y de esa misma estructura salen el Markdown, el
ODT y el RTF, en vez de repetir la deducción en cada formato.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import fitz

_NEGRITA = 1 << 4  # flag de span en negrita (PyMuPDF)


@dataclass(frozen=True)
class Tramo:
    """Trozo de texto con un formato uniforme."""

    texto: str
    negrita: bool = False


@dataclass(frozen=True)
class Bloque:
    """Párrafo, título o tabla, en orden de lectura."""

    tramos: tuple[Tramo, ...] = ()
    nivel: int = 0  # 1-3 si es título, 0 si es párrafo
    filas: tuple[tuple[str, ...], ...] = ()  # solo si es tabla

    @property
    def es_tabla(self) -> bool:
        return bool(self.filas)

    @property
    def es_titulo(self) -> bool:
        return self.nivel > 0

    @property
    def texto(self) -> str:
        return "".join(t.texto for t in self.tramos)


def tamano_base(doc: fitz.Document, indices: Sequence[int]) -> float:
    """Tamaño de fuente del cuerpo: el más frecuente, ponderado por longitud."""
    from collections import Counter

    conteo: Counter[float] = Counter()
    for idx in indices:
        for bloque in doc[idx].get_text("dict")["blocks"]:
            if bloque.get("type") != 0:
                continue
            for linea in bloque["lines"]:
                for span in linea["spans"]:
                    conteo[round(span["size"], 1)] += len(span["text"])
    return conteo.most_common(1)[0][0] if conteo else 11.0


def nivel_titulo(tam_max: float, tam_base: float) -> int:
    ratio = tam_max / tam_base if tam_base else 1.0
    if ratio >= 1.8:
        return 1
    if ratio >= 1.45:
        return 2
    if ratio >= 1.25:
        return 3
    return 0


def bloques_de(page: fitz.Page, tam_base: float) -> list[Bloque]:
    """Bloques de la página en orden de lectura (de arriba abajo)."""
    items: list[tuple[float, Bloque]] = []
    rects_tabla: list[fitz.Rect] = []

    for tabla in page.find_tables().tables:
        rect = fitz.Rect(tabla.bbox)
        rects_tabla.append(rect)
        filas = tuple(
            tuple((c or "").replace("\n", " ").strip() for c in fila)
            for fila in tabla.extract()
            if fila
        )
        if filas:
            items.append((rect.y0, Bloque(filas=filas)))

    for bruto in page.get_text("dict")["blocks"]:
        if bruto.get("type") != 0:  # solo bloques de texto
            continue
        rect_b = fitz.Rect(bruto["bbox"])
        if any(rect_b.intersects(rt) for rt in rects_tabla):
            continue  # su texto ya está en la tabla
        bloque = _bloque_de_texto(bruto, tam_base)
        if bloque is not None:
            items.append((rect_b.y0, bloque))

    items.sort(key=lambda it: it[0])
    return [bloque for _, bloque in items]


def _bloque_de_texto(bruto: dict[str, Any], tam_base: float) -> Bloque | None:
    tramos: list[Tramo] = []
    tam_max = 0.0
    for linea in bruto["lines"]:
        for span in linea["spans"]:
            tam_max = max(tam_max, span["size"])
            texto = span["text"]
            if not texto:
                continue
            negrita = bool(span["flags"] & _NEGRITA) and bool(texto.strip())
            if tramos and tramos[-1].negrita == negrita:
                tramos[-1] = Tramo(tramos[-1].texto + texto, negrita)
            else:
                tramos.append(Tramo(texto, negrita))
        if tramos and not tramos[-1].texto.endswith(" "):
            tramos[-1] = Tramo(tramos[-1].texto + " ", tramos[-1].negrita)

    unido = "".join(t.texto for t in tramos).strip()
    if not unido:
        return None
    nivel = nivel_titulo(tam_max, tam_base)
    if nivel:
        # Un título ya destaca por tamaño: la negrita interna no aporta nada.
        return Bloque(tramos=(Tramo(unido),), nivel=nivel)
    return Bloque(tramos=tuple(_recortar(tramos)))


def _recortar(tramos: list[Tramo]) -> list[Tramo]:
    """Quita el espacio sobrante al principio y al final del bloque."""
    limpios = [t for t in tramos if t.texto]
    if not limpios:
        return []
    limpios[0] = Tramo(limpios[0].texto.lstrip(), limpios[0].negrita)
    limpios[-1] = Tramo(limpios[-1].texto.rstrip(), limpios[-1].negrita)
    return [t for t in limpios if t.texto]
