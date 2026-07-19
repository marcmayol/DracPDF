"""Tests del controlador de colocación del sello de firma digital."""

from __future__ import annotations

from pathlib import Path

from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina
from lectorpdf.core.use_cases.firmar_digitalmente import FirmarDigitalmente
from lectorpdf.core.use_cases.renderizar_pagina import RenderizarPagina
from lectorpdf.ui.signature.digital_seal_layer import DigitalSealLayer
from lectorpdf.ui.viewer.viewer_widget import ViewerWidget
from tests.core.fakes import FakeDocumentRepository, FakeSignatureService


def _documento() -> Documento:
    return Documento(
        id="doc-1",
        ruta=Path("doc.pdf"),
        paginas=(Pagina(indice=0, ancho_pt=400.0, alto_pt=600.0),),
    )


def _entorno(
    documento: Documento, tmp_path: Path
) -> tuple[ViewerWidget, DigitalSealLayer, FakeSignatureService]:
    imagen = ImagenRenderizada(
        ancho_px=400, alto_px=600, datos=b"\x00" * (400 * 600 * 4), escala=1.0
    )
    repo = FakeDocumentRepository(documento=documento, imagen=imagen)
    visor = ViewerWidget(RenderizarPagina(repo))
    visor.resize(500, 700)
    servicio = FakeSignatureService()
    capa = DigitalSealLayer(visor, FirmarDigitalmente(servicio))
    return visor, capa, servicio


def _credencial(tmp_path: Path):  # type: ignore[no-untyped-def]
    from lectorpdf.core.domain.firma_digital import CredencialPKCS12

    p12 = tmp_path / "cert.p12"
    p12.write_bytes(b"pkcs12")
    return CredencialPKCS12(p12, "x")


def test_confirmar_firma_en_la_pagina_con_sello_visible(
    qapp: object, tmp_path: Path
) -> None:
    documento = _documento()
    visor, capa, servicio = _entorno(documento, tmp_path)
    visor.set_documento(documento)

    capa.iniciar_colocacion(documento, _credencial(tmp_path), "Conforme")
    assert capa.colocando() is True
    pagina = capa.confirmar()

    assert pagina == 0
    assert len(servicio.firmas) == 1
    doc_id, config, _ = servicio.firmas[0]
    assert doc_id == "doc-1"
    assert config.rect_pt is not None  # sello visible
    assert config.razon == "Conforme"
    assert capa.colocando() is False


def test_cancelar_no_firma(qapp: object, tmp_path: Path) -> None:
    documento = _documento()
    visor, capa, servicio = _entorno(documento, tmp_path)
    visor.set_documento(documento)

    capa.iniciar_colocacion(documento, _credencial(tmp_path), None)
    capa.cancelar()

    assert capa.colocando() is False
    assert servicio.firmas == []
