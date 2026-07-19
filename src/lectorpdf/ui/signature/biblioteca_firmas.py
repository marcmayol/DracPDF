"""Biblioteca de firmas guardadas del usuario.

Utilidad de la UI (no dominio): persistencia de conveniencia, análoga a
"recordar la última carpeta". Sin Qt, solo `pathlib`/`json`, para poder testearla
directa contra ficheros reales.

Formato: por cada firma, `<id>.png` (imagen) + `<id>.json` (metadatos
{nombre, creada}). El alta escribe el PNG primero y el JSON después; al listar se
ignoran los PNG sin sidecar, de modo que un cierre a mitad de alta deja como
mucho un PNG huérfano invisible, nunca una entrada que apunte a nada.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


class FirmaNoEncontrada(Exception):
    """No existe ninguna firma guardada con el id indicado."""


@dataclass(frozen=True)
class FirmaGuardada:
    id: str
    nombre: str
    creada: str  # ISO 8601 (UTC)
    ruta_png: Path


def directorio_por_defecto() -> Path:
    """~/.config/lectorpdf/firmas/ (según PLAN.md)."""
    return Path.home() / ".config" / "lectorpdf" / "firmas"


class BibliotecaFirmas:
    def __init__(self, directorio: Path) -> None:
        self._dir = directorio

    def guardar(self, nombre: str, png: bytes) -> FirmaGuardada:
        self._dir.mkdir(parents=True, exist_ok=True)
        firma_id = uuid.uuid4().hex
        creada = datetime.now(UTC).isoformat()

        # PNG primero, JSON después: el orden hace el alta atómica.
        (self._dir / f"{firma_id}.png").write_bytes(png)
        (self._dir / f"{firma_id}.json").write_text(
            json.dumps({"nombre": nombre, "creada": creada}), encoding="utf-8"
        )
        return FirmaGuardada(firma_id, nombre, creada, self._dir / f"{firma_id}.png")

    def listar(self) -> list[FirmaGuardada]:
        if not self._dir.exists():
            return []
        firmas: list[FirmaGuardada] = []
        for png_path in self._dir.glob("*.png"):
            firma_id = png_path.stem
            json_path = self._dir / f"{firma_id}.json"
            if not json_path.exists():
                continue  # PNG huérfano (alta a medias): se ignora
            datos = json.loads(json_path.read_text(encoding="utf-8"))
            firmas.append(
                FirmaGuardada(firma_id, datos["nombre"], datos["creada"], png_path)
            )
        firmas.sort(key=lambda f: f.creada)
        return firmas

    def cargar(self, firma_id: str) -> bytes:
        png_path = self._dir / f"{firma_id}.png"
        if not png_path.exists():
            raise FirmaNoEncontrada(firma_id)
        return png_path.read_bytes()

    def eliminar(self, firma_id: str) -> None:
        (self._dir / f"{firma_id}.png").unlink(missing_ok=True)
        (self._dir / f"{firma_id}.json").unlink(missing_ok=True)
