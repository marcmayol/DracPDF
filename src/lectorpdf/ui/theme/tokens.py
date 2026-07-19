"""Tokens de la identidad visual "Ladón", extraídos del diseño de Claude Design.

Única fuente de verdad de colores y medidas: ningún valor de color/tamaño debe
aparecer suelto por el código; todo sale de aquí. Un dataclass por tema
(claro/oscuro) para los colores, más métricas y tipografía compartidas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tema:
    """Paleta de un tema. Colores en hexadecimal (#RRGGBB)."""

    nombre: str
    es_oscuro: bool
    canvas: str  # fondo tras las páginas (QGraphicsView)
    bg: str  # ventana, diálogos
    surface: str  # toolbar, paneles, menús
    surface_2: str  # hover, filas alternas
    border: str  # bordes de 1px
    text: str
    text_muted: str
    accent: str  # rojo brasa
    accent_hover: str
    on_accent: str  # texto sobre acento
    sig_valid: str  # estado de firma válida (token semántico, no verde puro)
    sig_invalid: str
    sig_unknown: str


@dataclass(frozen=True)
class Radios:
    control: int = 4
    panel: int = 6
    dialogo: int = 8


@dataclass(frozen=True)
class Espaciado:
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    toolbar: int = 40
    statusbar: int = 24


@dataclass(frozen=True)
class Tipografia:
    familia_ui: tuple[str, ...] = ("Segoe UI", "Noto Sans", "Cantarell")
    familia_mono: tuple[str, ...] = ("JetBrains Mono", "Consolas")
    tam_base: int = 13
    tam_titulo: int = 15
    tam_meta: int = 12
    peso_normal: int = 400
    peso_enfasis: int = 600


RADIOS = Radios()
ESPACIADO = Espaciado()
TIPOGRAFIA = Tipografia()


TEMA_OSCURO = Tema(
    nombre="oscuro",
    es_oscuro=True,
    canvas="#14161A",
    bg="#1A1D23",
    surface="#22262E",
    surface_2="#2A2F39",
    border="#343A46",
    text="#E9EBF0",
    text_muted="#98A0B0",
    accent="#E0534A",
    accent_hover="#EA6E63",
    on_accent="#FFFFFF",
    sig_valid="#6FBF87",
    sig_invalid="#E07B6E",
    sig_unknown="#D9B45C",
)

TEMA_CLARO = Tema(
    nombre="claro",
    es_oscuro=False,
    canvas="#D8DAE0",
    bg="#F2F2F5",
    surface="#FFFFFF",
    surface_2="#E9EAEF",
    border="#C9CCD6",
    text="#22252C",
    text_muted="#6A7080",
    accent="#A83228",
    accent_hover="#8F251C",
    on_accent="#FFFFFF",
    sig_valid="#2E7D4F",
    sig_invalid="#B23B2E",
    sig_unknown="#96741F",
)

TEMAS: dict[str, Tema] = {TEMA_OSCURO.nombre: TEMA_OSCURO, TEMA_CLARO.nombre: TEMA_CLARO}
TEMA_POR_DEFECTO = TEMA_OSCURO  # el diseño pide oscuro por defecto


def tema_por_nombre(nombre: str) -> Tema:
    return TEMAS.get(nombre, TEMA_POR_DEFECTO)


def rgba(hex_color: str, alfa: float) -> str:
    """Convierte '#RRGGBB' + alfa (0..1) a 'rgba(r, g, b, a)' para el QSS.

    Permite derivar tintes translúcidos (p. ej. selección) del token de acento
    sin introducir un color nuevo.
    """
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alfa})"
