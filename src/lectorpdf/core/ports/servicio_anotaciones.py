"""Puerto de texto, anotaciones e imágenes sobre el documento (Fase 9).

Opera sobre el `documento_id` de sesión a través del registro compartido del
adaptador. Las operaciones que modifican el contenido (texto, corrección,
imágenes) se apuntan en un historial propio basado en snapshots; `deshacer` /
`rehacer` devuelven las páginas afectadas para que la UI invalide su render.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.anotaciones import (
    Color,
    Correccion,
    FuenteTexto,
    Nota,
    TextoNuevo,
    TipoMarcado,
)
from lectorpdf.core.domain.formularios import RectanguloPt


@runtime_checkable
class ServicioAnotaciones(Protocol):
    def anadir_texto(
        self, documento_id: str, pagina: int, texto: TextoNuevo
    ) -> None:
        """Estampa `texto` en `pagina` con una fuente OFL embebida. Marca cambios
        sin guardar y registra la operación para deshacer."""
        ...

    def marcar(
        self,
        documento_id: str,
        pagina: int,
        rects_pt: tuple[RectanguloPt, ...],
        tipo: TipoMarcado,
        color: Color,
    ) -> None:
        """Crea una anotación de marcado (resaltado/subrayado/tachado) estándar
        sobre `rects_pt`. Registra la operación para deshacer."""
        ...

    def anadir_nota(self, documento_id: str, pagina: int, nota: Nota) -> None:
        """Crea una nota adhesiva (anotación de texto emergente). Deshacible."""
        ...

    def anotacion_en(
        self, documento_id: str, pagina: int, x_pt: float, y_pt: float
    ) -> int | None:
        """Xref de la anotación bajo el punto (para el clic derecho), o None."""
        ...

    def eliminar_anotacion(self, documento_id: str, pagina: int, xref: int) -> None:
        """Elimina la anotación `xref` de `pagina`. Acción directa (no deshacible)."""
        ...

    def cabe_texto(
        self,
        documento_id: str,
        pagina: int,
        rect_pt: RectanguloPt,
        texto: str,
        fuente: FuenteTexto,
    ) -> bool:
        """True si `texto` cabe a lo ancho de `rect_pt` al tamaño que casa con la
        altura del tramo (para avisar del caso "no cabe" antes de corregir)."""
        ...

    def corregir_texto(
        self, documento_id: str, pagina: int, correccion: Correccion
    ) -> None:
        """Redacta el tramo (elimina de verdad el original) y escribe el texto
        nuevo en su sitio con fuente sustituta embebida, casando el tamaño con la
        altura del tramo. Lanza `TextoNoCabe` si no cabe y `reducir=False`."""
        ...

    def puede_deshacer(self, documento_id: str) -> bool: ...

    def puede_rehacer(self, documento_id: str) -> bool: ...

    def deshacer(self, documento_id: str) -> tuple[int, ...] | None:
        """Revierte la última operación de contenido. Devuelve las páginas a
        invalidar, o None si no había nada que deshacer."""
        ...

    def rehacer(self, documento_id: str) -> tuple[int, ...] | None: ...
