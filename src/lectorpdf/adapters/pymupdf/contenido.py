"""Adaptador de los servicios de contenido (Fase 8) sobre PyMuPDF.

Solo lectura del documento abierto vía el `RegistroDocumentos` compartido: nunca
lo muta ni lo cierra. Reúne búsqueda, y en tareas posteriores irá creciendo con
palabras/índice/enlaces/propiedades. Cada método satisface, por tipado
estructural, su puerto pequeño correspondiente.
"""

from __future__ import annotations

from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.contenido import (
    Coincidencia,
    EntradaIndice,
    PalabraTexto,
)
from lectorpdf.core.domain.formularios import RectanguloPt
from lectorpdf.core.domain.herramientas import Progreso


class PyMuPDFContenido:
    def __init__(self, registro: RegistroDocumentos) -> None:
        self._registro = registro

    def buscar(
        self,
        documento_id: str,
        termino: str,
        coincidir_mayusculas: bool = False,
        progreso: Progreso | None = None,
    ) -> tuple[Coincidencia, ...]:
        """Busca `termino` en todas las páginas. `search_for` es insensible a
        mayúsculas; si se pide coincidir, se filtra por el texto real del rect."""
        doc = self._registro.obtener(documento_id)
        total = doc.page_count
        resultados: list[Coincidencia] = []
        for indice in range(total):
            pagina = doc[indice]
            for rect in pagina.search_for(termino):
                if coincidir_mayusculas and termino not in pagina.get_textbox(rect):
                    continue
                resultados.append(
                    Coincidencia(
                        indice,
                        RectanguloPt(rect.x0, rect.y0, rect.x1, rect.y1),
                    )
                )
            if progreso is not None:
                progreso(indice + 1, total)  # puede lanzar OperacionCancelada
        return tuple(resultados)

    def palabras(self, documento_id: str, pagina: int) -> tuple[PalabraTexto, ...]:
        """Palabras de la página en orden de lectura. Cada tupla de `words` es
        (x0, y0, x1, y1, texto, bloque, linea, palabra)."""
        p = self._registro.obtener(documento_id)[pagina]
        return tuple(
            PalabraTexto(
                RectanguloPt(x0, y0, x1, y1),
                texto,
                bloque,
                linea,
            )
            for x0, y0, x1, y1, texto, bloque, linea, _ in p.get_text(
                "words", sort=True
            )
        )

    def indice(self, documento_id: str) -> tuple[EntradaIndice, ...]:
        """Índice (outline). `get_toc` da [nivel, título, página_1based]; la
        página se pasa a 0-based (-1 si la entrada no apunta a ninguna)."""
        doc = self._registro.obtener(documento_id)
        return tuple(
            EntradaIndice(nivel, titulo, pagina - 1 if pagina > 0 else -1)
            for nivel, titulo, pagina in doc.get_toc()
        )
