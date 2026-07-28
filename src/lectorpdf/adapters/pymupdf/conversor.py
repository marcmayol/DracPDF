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
from pathlib import Path

import fitz

from lectorpdf.adapters.pymupdf.estructura import Bloque, bloques_de, tamano_base
from lectorpdf.adapters.pymupdf.odt_salida import escribir_odt
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.adapters.pymupdf.rtf_salida import escribir_rtf
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
        base = tamano_base(doc, indices)
        partes: list[str] = []
        total = len(indices)
        for i, idx in enumerate(indices):
            pagina_md = _bloques_a_markdown(bloques_de(doc[idx], base))
            if pagina_md.strip():
                partes.append(pagina_md)
            if progreso is not None:
                progreso(i + 1, total)
        _escribir_texto_atomico(destino, "\n\n".join(partes) + "\n")

    def a_odt(
        self,
        documento_id: str,
        destino: Path,
        rango: Rango | None = None,
        progreso: Progreso | None = None,
    ) -> None:
        escribir_odt(self._estructura(documento_id, rango, progreso), destino)

    def a_rtf(
        self,
        documento_id: str,
        destino: Path,
        rango: Rango | None = None,
        progreso: Progreso | None = None,
    ) -> None:
        escribir_rtf(self._estructura(documento_id, rango, progreso), destino)

    def _estructura(
        self,
        documento_id: str,
        rango: Rango | None,
        progreso: Progreso | None,
    ) -> list[Bloque]:
        """Bloques de todas las páginas del rango, en orden de lectura."""
        doc = self._registro.obtener(documento_id)
        indices = self._indices(doc, rango)
        base = tamano_base(doc, indices)
        bloques: list[Bloque] = []
        total = len(indices)
        for i, idx in enumerate(indices):
            bloques.extend(bloques_de(doc[idx], base))
            if progreso is not None:
                progreso(i + 1, total)
        return bloques

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


def _bloques_a_markdown(bloques: list[Bloque]) -> str:
    partes: list[str] = []
    for bloque in bloques:
        if bloque.es_tabla:
            partes.append(_tabla_markdown([list(f) for f in bloque.filas]))
        elif bloque.es_titulo:
            partes.append("#" * bloque.nivel + " " + bloque.texto.strip())
        else:
            texto = "".join(
                f"**{t.texto}**" if t.negrita else t.texto for t in bloque.tramos
            ).strip()
            if texto:
                partes.append(texto)
    return "\n\n".join(p for p in partes if p)


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
