"""Genera un certificado PKCS#12 autofirmado de prueba (no se versiona).

Uso:
    uv run python scripts/generar_certificado.py [directorio] [contraseña]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.adapters.certificado_prueba import (  # noqa: E402
    CONTRASENA_POR_DEFECTO,
    generar_pkcs12,
)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    directorio = Path(argv[1]) if len(argv) > 1 else Path("certificado_prueba")
    contrasena = argv[2] if len(argv) > 2 else CONTRASENA_POR_DEFECTO

    p12, der = generar_pkcs12(directorio, contrasena)
    print(f"PKCS#12 (clave + cert): {p12}")
    print(f"Certificado público DER: {der}")
    print(f"Contraseña: {contrasena}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
