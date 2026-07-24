"""Puerto del servicio de actualizaciones (Fase 10).

Abstrae la red y el lanzamiento del instalador. El adaptador (urllib +
subprocess) implementa esto; el caso de uso solo conoce este contrato y tolera
cualquier excepción que aquí se lance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from lectorpdf.core.domain.actualizacion import Manifiesto


@runtime_checkable
class ActualizadorService(Protocol):
    def descargar_manifiesto(
        self, etag: str | None = None
    ) -> tuple[Manifiesto | None, str | None]:
        """Descarga y parsea el manifiesto. Devuelve ``(manifiesto, nuevo_etag)``.

        Si el servidor responde 304 (ETag sin cambios), devuelve ``(None, etag)``
        sin descargar cuerpo. Puede lanzar en caso de red/JSON/servidor; el caso
        de uso captura esas excepciones y las convierte en ``ERROR``."""
        ...

    def descargar_instalador(self, url: str, destino: Path) -> Path:
        """Descarga el instalador a ``destino`` y devuelve la ruta."""
        ...

    def sha256(self, ruta: Path) -> str:
        """SHA256 en hexadecimal (minúsculas) del fichero."""
        ...

    def lanzar_instalador(self, ruta: Path) -> None:
        """Lanza el instalador en modo silencioso por usuario. No retorna nada;
        la UI cierra la app a continuación."""
        ...
