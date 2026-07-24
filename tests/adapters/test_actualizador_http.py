"""Tests del adaptador HTTP de actualizaciones contra un servidor local.

Sin red real: se levanta un http.server en localhost en un hilo del test, que
sirve un manifiesto, respeta el ETag (304), y ofrece rutas rotas/erróneas.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from lectorpdf.adapters.red.actualizador_http import ActualizadorHTTP

_ETAG = '"v0.3.0"'
_MANIFIESTO = {
    "version": "0.3.0",
    "url": "http://x/setup.exe",
    "sha256": "00" * 32,
    "notas": "Novedades 0.3.0",
    "check_horas": 12,
}
_SETUP_BYTES = b"instalador-de-prueba" * 100


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args: object) -> None:  # silencia el log del server
        pass

    def do_GET(self) -> None:  # noqa: N802 (API de la stdlib)
        if self.path == "/updates.json":
            if self.headers.get("If-None-Match") == _ETAG:
                self.send_response(304)
                self.end_headers()
                return
            cuerpo = json.dumps(_MANIFIESTO).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("ETag", _ETAG)
            self.end_headers()
            self.wfile.write(cuerpo)
        elif self.path == "/broken.json":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{ esto no es json")
        elif self.path == "/setup.exe":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(_SETUP_BYTES)
        else:  # cualquier otra ruta: error de servidor
            self.send_response(500)
            self.end_headers()


@pytest.fixture
def servidor() -> Iterator[str]:
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo.start()
    host, puerto = httpd.server_address
    try:
        yield f"http://127.0.0.1:{puerto}"
    finally:
        httpd.shutdown()


def test_descarga_y_parsea_manifiesto(servidor: str) -> None:
    act = ActualizadorHTTP(f"{servidor}/updates.json")
    manifiesto, etag = act.descargar_manifiesto()
    assert manifiesto is not None
    assert manifiesto.version == "0.3.0"
    assert manifiesto.notas == "Novedades 0.3.0"
    assert manifiesto.check_horas == 12
    assert etag == _ETAG


def test_etag_sin_cambios_devuelve_304_sin_cuerpo(servidor: str) -> None:
    act = ActualizadorHTTP(f"{servidor}/updates.json")
    manifiesto, etag = act.descargar_manifiesto(etag=_ETAG)
    assert manifiesto is None  # 304: no hay cuerpo
    assert etag == _ETAG


def test_servidor_con_error_lanza(servidor: str) -> None:
    from urllib.error import HTTPError

    act = ActualizadorHTTP(f"{servidor}/no-existe.json")
    with pytest.raises(HTTPError):
        act.descargar_manifiesto()


def test_json_malformado_lanza(servidor: str) -> None:
    act = ActualizadorHTTP(f"{servidor}/broken.json")
    with pytest.raises(json.JSONDecodeError):
        act.descargar_manifiesto()


def test_sin_servidor_lanza_urlerror() -> None:
    from urllib.error import URLError

    # Puerto donde no escucha nadie.
    act = ActualizadorHTTP("http://127.0.0.1:1/updates.json", timeout=2)
    with pytest.raises(URLError):
        act.descargar_manifiesto()


def test_descarga_instalador_y_sha256(servidor: str, tmp_path: Path) -> None:
    act = ActualizadorHTTP()
    destino = tmp_path / "setup.exe"
    act.descargar_instalador(f"{servidor}/setup.exe", destino)
    assert destino.read_bytes() == _SETUP_BYTES
    assert act.sha256(destino) == hashlib.sha256(_SETUP_BYTES).hexdigest()
