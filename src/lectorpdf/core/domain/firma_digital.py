"""Entidades de dominio para la firma digital (PAdES) y su verificación."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from lectorpdf.core.domain.formularios import RectanguloPt


class CredencialFirma:
    """Credencial con la que firmar. Concepto abstracto: hoy solo PKCS#12.

    Se deja como base para poder añadir PKCS#11 (tokens hardware: DNIe/FNMT)
    como una variante nueva sin tocar el core ni la UI.
    """


@dataclass(frozen=True)
class CredencialPKCS12(CredencialFirma):
    """Certificado en fichero PKCS#12 (.p12/.pfx) protegido con contraseña."""

    ruta: Path
    contrasena: str


@dataclass(frozen=True)
class ConfigFirma:
    """Parámetros de una operación de firma."""

    pagina: int
    rect_pt: RectanguloPt | None = None  # None = firma invisible; si no, sello visible
    razon: str | None = None
    usar_tsa: bool = False
    url_tsa: str | None = None


class EstadoFirma(Enum):
    VALIDA = auto()  # íntegra, cubre todo el documento y firmante de confianza
    INVALIDA = auto()  # rota, o el documento se modificó tras la firma
    DESCONOCIDA = auto()  # íntegra pero la cadena de confianza no es verificable


@dataclass(frozen=True)
class ResultadoVerificacion:
    firmante: str
    estado: EstadoFirma
    cubre_todo_el_documento: bool
    sellada_en_tiempo: bool
    motivo: str


def anclas_por_defecto() -> tuple[Path, ...]:
    return ()
