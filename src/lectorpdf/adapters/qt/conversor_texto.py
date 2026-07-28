"""Adaptador de `ConversorTexto` con Qt (Markdown, HTML o texto plano → PDF).

Misma cadena que Word → PDF: QTextDocument compone y pagina, QPdfWriter escribe.
El formato se decide por la extensión, que el caso de uso ya ha validado.

En HTML se fija la URL base al directorio del fichero, para que las imágenes y
hojas de estilo referidas con rutas relativas se resuelvan; nada se descarga de
la red, Qt solo abre ficheros locales.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QTextDocument

from lectorpdf.adapters.qt.escritura_pdf import escribir_pdf
from lectorpdf.core.domain.conversion import ConfigPagina
from lectorpdf.core.domain.herramientas import Progreso

_MARKDOWN = (".md", ".markdown")
_HTML = (".html", ".htm")


def leer_texto(ruta: Path) -> str:
    """Lee el fichero como UTF-8 y, si no lo es, como cp1252.

    Los .txt y .html guardados por programas de Windows suelen venir en la
    codificación del sistema; fallar con un rastro de UnicodeDecodeError no
    ayudaría a nadie.
    """
    datos = ruta.read_bytes()
    for codificacion in ("utf-8-sig", "cp1252"):
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return datos.decode("utf-8", errors="replace")


class ConversorTextoQt:
    def a_pdf(
        self,
        ruta: Path,
        destino: Path,
        config: ConfigPagina,
        progreso: Progreso | None = None,
    ) -> None:
        texto = leer_texto(ruta)
        documento = QTextDocument()
        sufijo = ruta.suffix.lower()
        if sufijo in _MARKDOWN:
            documento.setMarkdown(texto)
        elif sufijo in _HTML:
            documento.setBaseUrl(QUrl.fromLocalFile(str(ruta.parent) + "/"))
            documento.setHtml(texto)
        else:
            documento.setPlainText(texto)
        escribir_pdf(documento, destino, config)
        if progreso is not None:
            progreso(1, 1)  # conversión en un paso
