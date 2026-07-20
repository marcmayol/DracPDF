"""Entidades de dominio para los campos de formulario (AcroForm).

Sin dependencias de infraestructura. Las coordenadas van en puntos PDF con el
mismo convenio que usa PyMuPDF: origen arriba-izquierda, eje y hacia abajo.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TipoCampo(Enum):
    TEXTO = auto()
    CASILLA = auto()  # checkbox
    RADIO = auto()  # radio button (una opción de un grupo)
    COMBO = auto()  # desplegable
    LISTA = auto()  # listbox


@dataclass(frozen=True)
class RectanguloPt:
    """Rectángulo en puntos PDF (origen arriba-izquierda)."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def ancho(self) -> float:
        return self.x1 - self.x0

    @property
    def alto(self) -> float:
        return self.y1 - self.y0


@dataclass(frozen=True)
class CambioValor:
    """Campo afectado por deshacer/rehacer y el valor que queda tras la operación."""

    campo_id: str
    valor: str


@dataclass(frozen=True)
class CampoFormulario:
    """Un widget de formulario. `id` es de sesión: f"{pagina}:{indice_widget}"."""

    id: str
    nombre: str
    tipo: TipoCampo
    pagina: int
    rect_pt: RectanguloPt
    valor: str
    opciones: tuple[str, ...] = ()
    estado_activado: str | None = None  # casilla/radio: estado "on" (p. ej. "Yes")
    solo_lectura: bool = False
