"""Entidades de dominio para las conversiones de formato (Fase 7).

Sin dependencias de infraestructura. El rango de páginas se reutiliza de
`herramientas.Rango` (1-based, inclusivo). `ConfigPagina` describe el tamaño y
los márgenes del PDF generado desde Word.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


@dataclass(frozen=True)
class ConfigPagina:
    """Tamaño de página y margen (en milímetros) para Word→PDF."""

    ancho_mm: float = 210.0  # A4 por defecto
    alto_mm: float = 297.0
    margen_mm: float = 20.0

    def __post_init__(self) -> None:
        if self.ancho_mm <= 0 or self.alto_mm <= 0 or self.margen_mm < 0:
            raise ValueError("Dimensiones o margen inválidos")


A4 = ConfigPagina()
CARTA = ConfigPagina(ancho_mm=215.9, alto_mm=279.4)


class AjusteImagen(Enum):
    """Cómo se acomoda cada imagen en su página al convertir imágenes a PDF."""

    #: Cada página adopta el tamaño de su imagen (sin márgenes ni recorte).
    TAMANO_IMAGEN = auto()
    #: Todas las páginas con el tamaño de `ConfigPagina`; la imagen se escala
    #: dentro de los márgenes conservando su proporción.
    PAGINA_FIJA = auto()


#: Extensiones que se convierten a PDF por la cadena Qt (texto y ODT).
EXTENSIONES_TEXTO: tuple[str, ...] = (
    ".md",
    ".markdown",
    ".html",
    ".htm",
    ".txt",
    ".odt",
    ".rtf",
)

#: Formatos de texto que NO se convierten, con la salida que se le ofrece al
#: usuario. Leerlos exigiría Word o LibreOffice instalados, y DracPDF es un
#: ejecutable autocontenido; callar y no mostrar el fichero sería peor.
FORMATOS_SIN_SOPORTE: dict[str, str] = {
    ".doc": (
        "Los documentos de Word 97-2003 (.doc) no se pueden convertir aquí.\n\n"
        "Ábrelo en Word y guárdalo como .docx, o expórtalo a PDF desde el propio "
        "Word."
    ),
    ".pages": (
        "Los documentos de Pages (.pages) no se pueden convertir aquí.\n\n"
        "Expórtalo desde Pages a Word (.docx) o a PDF."
    ),
    ".wpd": (
        "Los documentos de WordPerfect (.wpd) no se pueden convertir aquí.\n\n"
        "Ábrelo en su programa original y guárdalo como .docx o .rtf."
    ),
}

#: Extensiones de imagen que el motor sabe abrir (las de MuPDF).
EXTENSIONES_IMAGEN: tuple[str, ...] = (
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".pnm",
    ".pgm",
    ".ppm",
    ".pbm",
    ".jxr",
    ".jpx",
    ".jp2",
    ".psd",
)
