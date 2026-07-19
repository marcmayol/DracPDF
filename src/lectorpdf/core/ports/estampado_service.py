"""Puerto de estampado de imágenes sobre el documento (firma dibujada).

Comparte el `documento_id` de sesión con los demás puertos: opera sobre el mismo
documento a través del registro compartido del adaptador.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.formularios import RectanguloPt


@runtime_checkable
class EstampadoService(Protocol):
    def estampar_imagen(
        self,
        documento_id: str,
        pagina: int,
        rect_pt: RectanguloPt,
        imagen_png: bytes,
    ) -> None:
        """Inserta `imagen_png` en `pagina` dentro de `rect_pt` (puntos PDF),
        conservando la transparencia. Marca el documento con cambios sin guardar.
        """
        ...
