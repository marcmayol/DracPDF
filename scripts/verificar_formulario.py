"""Criterio de aceptación de la Fase 2.

Genera un formulario con un campo de cada tipo, lo rellena a través de la pila
real (casos de uso + adaptador PyMuPDF), guarda de forma incremental, lo reabre
en una sesión nueva y verifica que los valores persisten.

Uso:
    uv run python scripts/verificar_formulario.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.form_service import PyMuPDFFormService
from lectorpdf.adapters.pymupdf.registro import RegistroDocumentos
from lectorpdf.core.domain.formularios import CampoFormulario
from lectorpdf.core.domain.modelos import Documento
from lectorpdf.core.use_cases.abrir_documento import AbrirDocumento
from lectorpdf.core.use_cases.guardar_formulario import GuardarFormulario
from lectorpdf.core.use_cases.listar_campos import ListarCampos
from lectorpdf.core.use_cases.rellenar_campo import RellenarCampo

# El generador de fixtures vive en tests/; se añade la raíz del repo al path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.adapters.generar_fixtures_formularios import (  # noqa: E402
    generar_formulario_completo,
)


def _abrir(ruta: Path) -> tuple[Documento, PyMuPDFFormService, RegistroDocumentos]:
    registro = RegistroDocumentos()
    documento = AbrirDocumento(PyMuPDFDocumentRepository(registro)).ejecutar(ruta)
    return documento, PyMuPDFFormService(registro), registro


def _por_nombre(campos: tuple[CampoFormulario, ...], nombre: str) -> CampoFormulario:
    return next(c for c in campos if c.nombre == nombre)


def main() -> int:
    ruta = Path(tempfile.gettempdir()) / "acept_formulario.pdf"
    generar_formulario_completo(ruta)

    # --- Sesión 1: rellenar y guardar incremental ---
    documento, servicio, registro = _abrir(ruta)
    rellenar = RellenarCampo(servicio)
    campos = ListarCampos(servicio).ejecutar(documento)

    radio = [c for c in campos if c.nombre == "genero"][1]  # segunda opción
    esperado = {
        "nombre": "Marc Mayol",
        "pais": "FR",
        "color": "verde",
    }

    rellenar.ejecutar(documento, _por_nombre(campos, "nombre"), esperado["nombre"])
    rellenar.ejecutar(documento, _por_nombre(campos, "pais"), esperado["pais"])
    rellenar.ejecutar(documento, _por_nombre(campos, "color"), esperado["color"])
    acepta = _por_nombre(campos, "acepta")
    assert acepta.estado_activado is not None
    rellenar.ejecutar(documento, acepta, acepta.estado_activado)
    assert radio.estado_activado is not None
    rellenar.ejecutar(documento, radio, radio.estado_activado)

    guardar = GuardarFormulario(servicio)
    assert guardar.hay_cambios_sin_guardar(documento) is True
    guardar.ejecutar(documento)  # incremental in situ
    assert guardar.hay_cambios_sin_guardar(documento) is False
    registro.cerrar(documento.id)

    # --- Sesión 2: reabrir y verificar ---
    documento2, servicio2, registro2 = _abrir(ruta)
    campos2 = ListarCampos(servicio2).ejecutar(documento2)
    valores = {c.nombre: c.valor for c in campos2}
    radios2 = [c for c in campos2 if c.nombre == "genero"]

    filas = [
        ("nombre (texto)", esperado["nombre"], valores["nombre"]),
        ("pais (combo)", esperado["pais"], valores["pais"]),
        ("color (lista)", esperado["color"], valores["color"]),
        ("acepta (casilla)", acepta.estado_activado, valores["acepta"]),
        ("genero (radio 1)", "Off", radios2[0].valor),
        ("genero (radio 2)", radio.estado_activado, radios2[1].valor),
    ]

    print("-" * 60)
    print(f"{'Campo':<20}{'Escrito':<18}{'Reabierto':<18}")
    print("-" * 60)
    ok = True
    for nombre, escrito, leido in filas:
        marca = "OK" if escrito == leido else "FALLO"
        if escrito != leido:
            ok = False
        print(f"{nombre:<20}{str(escrito):<18}{str(leido):<18}{marca}")
    print("-" * 60)
    registro2.cerrar(documento2.id)

    print("RESULTADO:", "OK" if ok else "FALLO")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
