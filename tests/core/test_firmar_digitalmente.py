"""Tests del caso de uso FirmarDigitalmente con un fake del servicio."""

from __future__ import annotations

from pathlib import Path

import pytest

from lectorpdf.core.domain.errores import CredencialInvalida, PaginaFueraDeRango
from lectorpdf.core.domain.firma_digital import ConfigFirma, CredencialPKCS12
from lectorpdf.core.domain.modelos import Documento, Pagina
from lectorpdf.core.use_cases.firmar_digitalmente import FirmarDigitalmente
from tests.core.fakes import FakeSignatureService


def _documento(num_paginas: int = 3) -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=tuple(
            Pagina(indice=i, ancho_pt=400.0, alto_pt=600.0) for i in range(num_paginas)
        ),
    )


def _credencial(tmp_path: Path) -> CredencialPKCS12:
    ruta = tmp_path / "cert.p12"
    ruta.write_bytes(b"pkcs12")  # el fake no lo abre, solo comprueba que existe
    return CredencialPKCS12(ruta=ruta, contrasena="x")


def test_firma_delegando_en_el_servicio(tmp_path: Path) -> None:
    servicio = FakeSignatureService()
    config = ConfigFirma(pagina=0, razon="Conforme")

    FirmarDigitalmente(servicio).ejecutar(_documento(), config, _credencial(tmp_path))

    assert len(servicio.firmas) == 1
    doc_id, cfg, _ = servicio.firmas[0]
    assert doc_id == "doc-1"
    assert cfg.razon == "Conforme"


def test_pagina_fuera_de_rango(tmp_path: Path) -> None:
    servicio = FakeSignatureService()

    with pytest.raises(PaginaFueraDeRango):
        FirmarDigitalmente(servicio).ejecutar(
            _documento(3), ConfigFirma(pagina=9), _credencial(tmp_path)
        )
    assert servicio.firmas == []


def test_certificado_inexistente_es_credencial_invalida(tmp_path: Path) -> None:
    servicio = FakeSignatureService()
    credencial = CredencialPKCS12(ruta=tmp_path / "no_existe.p12", contrasena="x")

    with pytest.raises(CredencialInvalida):
        FirmarDigitalmente(servicio).ejecutar(_documento(), ConfigFirma(pagina=0), credencial)
    assert servicio.firmas == []
