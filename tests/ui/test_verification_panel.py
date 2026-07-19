"""Tests del panel de verificación de firmas."""

from __future__ import annotations

from lectorpdf.core.domain.firma_digital import EstadoFirma, ResultadoVerificacion
from lectorpdf.ui.signature.verification_panel import VerificationPanel


def _resultado(estado: EstadoFirma) -> ResultadoVerificacion:
    return ResultadoVerificacion(
        firmante="Ana Firma",
        estado=estado,
        cubre_todo_el_documento=estado == EstadoFirma.VALIDA,
        sellada_en_tiempo=False,
        motivo="motivo",
    )


def test_sin_firmas_muestra_un_aviso(qapp: object) -> None:
    panel = VerificationPanel()

    panel.mostrar(())

    assert panel.filas() == 1
    assert "no tiene firmas" in panel.item(0).text().lower()


def test_muestra_una_fila_por_firma(qapp: object) -> None:
    panel = VerificationPanel()

    panel.mostrar(
        (_resultado(EstadoFirma.VALIDA), _resultado(EstadoFirma.INVALIDA))
    )

    assert panel.filas() == 2
    assert "VÁLIDA" in panel.item(0).text()
    assert "INVÁLIDA" in panel.item(1).text()
