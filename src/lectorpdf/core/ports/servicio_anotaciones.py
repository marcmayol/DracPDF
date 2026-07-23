"""Puerto de texto, anotaciones e imágenes sobre el documento (Fase 9).

Opera sobre el `documento_id` de sesión a través del registro compartido del
adaptador. Las operaciones que modifican el contenido (texto, corrección,
imágenes) se apuntan en un historial propio basado en snapshots; `deshacer` /
`rehacer` devuelven las páginas afectadas para que la UI invalide su render.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.anotaciones import Color, TextoNuevo, TipoMarcado
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

    def anotacion_en(
        self, documento_id: str, pagina: int, x_pt: float, y_pt: float
    ) -> int | None:
        """Xref de la anotación bajo el punto (para el clic derecho), o None."""
        ...

    def eliminar_anotacion(self, documento_id: str, pagina: int, xref: int) -> None:
        """Elimina la anotación `xref` de `pagina`. Acción directa (no deshacible)."""
        ...

    def puede_deshacer(self, documento_id: str) -> bool: ...

    def puede_rehacer(self, documento_id: str) -> bool: ...

    def deshacer(self, documento_id: str) -> tuple[int, ...] | None:
        """Revierte la última operación de contenido. Devuelve las páginas a
        invalidar, o None si no había nada que deshacer."""
        ...

    def rehacer(self, documento_id: str) -> tuple[int, ...] | None: ...
