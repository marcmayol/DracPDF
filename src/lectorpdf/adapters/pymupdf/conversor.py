"""Adaptador de `ConversorPDF` sobre PyMuPDF (conversiones salientes).

Lee el documento abierto del registro compartido (estado actual en memoria, no el
de disco) y lo convierte. HTML y Markdown usan fitz directamente; Word delega en
el módulo aislado de pdf2docx. Las conversiones no mutan el original: se permiten
aunque esté firmado.
"""

from __future__ import annotations

import base64
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import fitz

from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.herramientas import Progreso, Rango

_RE_IMAGEN = re.compile(r'src="data:image/([^;]+);base64,([^"]+)"')
_NEGRITA = 1 << 4  # flag de span en negrita (PyMuPDF)


class ConversorFitz:
    def __init__(self, registro: RegistroDocumentos) -> None:
        self._registro = registro

    def _indices(self, doc: fitz.Document, rango: Rango | None) -> list[int]:
        if rango is None:
            return list(range(doc.page_count))
        inicio = max(0, rango.inicio - 1)
        fin = min(doc.page_count, rango.fin)
        return list(range(inicio, fin))

    def a_word(
        self,
        documento_id: str,
        destino: Path,
        rango: Rango | None = None,
        progreso: Progreso | None = None,
    ) -> None:
        # pdf2docx trabaja sobre un fichero; se vuelca el estado actual del
        # documento (incluye ediciones sin guardar) a un PDF temporal.
        from lectorpdf.adapters.pdf2docx.pdf_a_docx import convertir

        doc = self._registro.obtener(documento_id)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            temporal = Path(tf.name)
        try:
            doc.save(str(temporal))
            convertir(temporal, destino, rango, progreso)
        finally:
            temporal.unlink(missing_ok=True)

    def a_html(
        self,
        documento_id: str,
        destino: Path,
        rango: Rango | None = None,
        imagenes_embebidas: bool = True,
        progreso: Progreso | None = None,
    ) -> None:
        doc = self._registro.obtener(documento_id)
        indices = self._indices(doc, rango)
        partes: list[str] = []
        total = len(indices)
        for i, idx in enumerate(indices):
            partes.append(doc[idx].get_text("html"))
            if progreso is not None:
                progreso(i + 1, total)
        html = _envolver_html(partes, destino.stem)
        if not imagenes_embebidas:
            html = _extraer_imagenes(html, destino)
        _escribir_texto_atomico(destino, html)

    def a_markdown(
        self,
        documento_id: str,
        destino: Path,
        rango: Rango | None = None,
        progreso: Progreso | None = None,
    ) -> None:
        doc = self._registro.obtener(documento_id)
        indices = self._indices(doc, rango)
        tam_base = _tamano_base(doc, indices)
        partes: list[str] = []
        total = len(indices)
        for i, idx in enumerate(indices):
            pagina_md = _pagina_a_markdown(doc[idx], tam_base)
            if pagina_md.strip():
                partes.append(pagina_md)
            if progreso is not None:
                progreso(i + 1, total)
        _escribir_texto_atomico(destino, "\n\n".join(partes) + "\n")

    def es_escaneado(self, documento_id: str) -> bool:
        """True si ninguna página tiene texto extraíble (PDF escaneado): la
        conversión saldría vacía. Un documento sin páginas no es escaneado."""
        doc = self._registro.obtener(documento_id)
        if doc.page_count == 0:
            return False
        return all(not doc[i].get_text("text").strip() for i in range(doc.page_count))


def _envolver_html(paginas: list[str], titulo: str) -> str:
    """Envuelve el HTML por página (que fitz da como fragmentos) en un documento
    HTML completo, con las páginas separadas por una regla."""
    cuerpo = '\n<hr class="salto-pagina">\n'.join(paginas)
    return (
        "<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{titulo}</title>\n</head>\n<body>\n{cuerpo}\n</body>\n</html>\n"
    )


def _extraer_imagenes(html: str, destino: Path) -> str:
    """Mueve las imágenes embebidas (data URI) a una carpeta aneja y reescribe los
    src a rutas relativas."""
    carpeta = destino.with_name(f"{destino.stem}_imagenes")
    carpeta.mkdir(parents=True, exist_ok=True)
    contador = {"n": 0}

    def reemplazar(m: re.Match[str]) -> str:
        extension = m.group(1).split("+")[0]
        nombre = f"img_{contador['n']}.{extension}"
        contador["n"] += 1
        (carpeta / nombre).write_bytes(base64.b64decode(m.group(2)))
        return f'src="{carpeta.name}/{nombre}"'

    return _RE_IMAGEN.sub(reemplazar, html)


def _escribir_texto_atomico(destino: Path, texto: str) -> None:
    tmp = destino.with_name(destino.name + ".tmp")
    tmp.write_text(texto, encoding="utf-8")
    os.replace(tmp, destino)


def _tamano_base(doc: fitz.Document, indices: list[int]) -> float:
    """Tamaño de fuente del cuerpo = el más frecuente (ponderado por longitud de
    texto), para comparar con él los títulos."""
    conteo: Counter[float] = Counter()
    for idx in indices:
        for bloque in doc[idx].get_text("dict")["blocks"]:
            if bloque.get("type") != 0:
                continue
            for linea in bloque["lines"]:
                for span in linea["spans"]:
                    conteo[round(span["size"], 1)] += len(span["text"])
    return conteo.most_common(1)[0][0] if conteo else 11.0


def _pagina_a_markdown(page: fitz.Page, tam_base: float) -> str:
    items: list[tuple[float, str]] = []
    rects_tabla: list[fitz.Rect] = []
    for tabla in page.find_tables().tables:
        rect = fitz.Rect(tabla.bbox)
        rects_tabla.append(rect)
        items.append((rect.y0, _tabla_markdown(tabla.extract())))

    for bloque in page.get_text("dict")["blocks"]:
        if bloque.get("type") != 0:  # solo bloques de texto
            continue
        rect_b = fitz.Rect(bloque["bbox"])
        if any(rect_b.intersects(rt) for rt in rects_tabla):
            continue  # su texto ya está en la tabla
        md = _bloque_markdown(bloque, tam_base)
        if md:
            items.append((rect_b.y0, md))

    items.sort(key=lambda it: it[0])  # orden de lectura (vertical)
    return "\n\n".join(md for _, md in items if md)


def _bloque_markdown(bloque: dict[str, Any], tam_base: float) -> str:
    lineas: list[str] = []
    tam_max = 0.0
    for linea in bloque["lines"]:
        partes: list[str] = []
        for span in linea["spans"]:
            texto = span["text"]
            tam_max = max(tam_max, span["size"])
            if span["flags"] & _NEGRITA and texto.strip():
                partes.append(f"**{texto}**")
            else:
                partes.append(texto)
        lineas.append("".join(partes))
    texto = " ".join(t.strip() for t in lineas if t.strip()).strip()
    if not texto:
        return ""
    nivel = _nivel_titulo(tam_max, tam_base)
    if nivel:  # un título ya destaca por tamaño; no dupliques con negrita
        return "#" * nivel + " " + texto.replace("**", "")
    return texto


def _nivel_titulo(tam_max: float, tam_base: float) -> int:
    ratio = tam_max / tam_base if tam_base else 1.0
    if ratio >= 1.8:
        return 1
    if ratio >= 1.45:
        return 2
    if ratio >= 1.25:
        return 3
    return 0


def _tabla_markdown(filas: list[list[str | None]]) -> str:
    limpias = [
        [(c or "").replace("\n", " ").strip() for c in fila] for fila in filas if fila
    ]
    if not limpias:
        return ""
    ncols = max(len(f) for f in limpias)

    def fila_md(f: list[str]) -> str:
        celdas = (f + [""] * ncols)[:ncols]
        return "| " + " | ".join(celdas) + " |"

    lineas = [fila_md(limpias[0]), "| " + " | ".join(["---"] * ncols) + " |"]
    lineas += [fila_md(f) for f in limpias[1:]]
    return "\n".join(lineas)
