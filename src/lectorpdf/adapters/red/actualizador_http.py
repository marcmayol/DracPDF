"""Adaptador HTTP de `ActualizadorService` (Fase 10).

Usa solo la biblioteca estándar (urllib, hashlib, subprocess). La app instalada
solo conoce la URL del manifiesto: nunca la API de GitHub. Las comprobaciones sin
novedad no descargan cuerpo gracias al ETag (cabecera If-None-Match → 304).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path
from urllib.error import HTTPError

from lectorpdf.core.domain.actualizacion import Manifiesto

#: Única fuente que conoce la app instalada: el manifiesto en GitHub Pages.
URL_MANIFIESTO = "https://marcmayol.github.io/DracPDF/updates.json"

#: Flags del instalador Inno: barra de progreso (no VERYSILENT), cierre y
#: reapertura ordenados de la app.
_FLAGS_INSTALADOR = ("/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS")

_TIMEOUT_S = 15


class ActualizadorHTTP:
    def __init__(
        self, url_manifiesto: str = URL_MANIFIESTO, timeout: int = _TIMEOUT_S
    ) -> None:
        self._url = url_manifiesto
        self._timeout = timeout

    def descargar_manifiesto(
        self, etag: str | None = None
    ) -> tuple[Manifiesto | None, str | None]:
        req = urllib.request.Request(self._url)  # noqa: S310 (URL propia, https)
        if etag:
            req.add_header("If-None-Match", etag)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                datos = resp.read()
                nuevo_etag = resp.headers.get("ETag")
        except HTTPError as exc:
            if exc.code == 304:  # ETag sin cambios: no hay cuerpo
                return None, etag
            raise
        return _parsear(datos), nuevo_etag

    def descargar_instalador(self, url: str, destino: Path) -> Path:
        with (
            urllib.request.urlopen(url, timeout=self._timeout) as resp,  # noqa: S310
            destino.open("wb") as f,
        ):
            shutil.copyfileobj(resp, f)
        return destino

    def sha256(self, ruta: Path) -> str:
        h = hashlib.sha256()
        with ruta.open("rb") as f:
            for bloque in iter(lambda: f.read(65536), b""):
                h.update(bloque)
        return h.hexdigest()

    def lanzar_instalador(self, ruta: Path) -> None:
        subprocess.Popen([str(ruta), *_FLAGS_INSTALADOR])  # noqa: S603


def _parsear(datos: bytes) -> Manifiesto:
    d = json.loads(datos)
    return Manifiesto(
        version=str(d["version"]),
        url=str(d["url"]),
        sha256=str(d["sha256"]),
        notas=str(d.get("notas", "")),
        check_horas=int(d.get("check_horas", 24)),
        canal=d.get("canal"),
        porcentaje_despliegue=d.get("porcentaje_despliegue"),
    )
