"""Tests del panel de verificación de firmas (tarjetas con tokens semánticos)."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel

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


def _primer_frame(panel: VerificationPanel) -> QFrame:
    for i in range(panel.layout().count()):
        widget = panel.layout().itemAt(i).widget()
        if isinstance(widget, QFrame):
            return widget
    raise AssertionError("No hay tarjeta")


def test_sin_firmas_muestra_un_aviso(qapp: object) -> None:
    panel = VerificationPanel()

    panel.mostrar(())

    assert panel.tarjetas() == 0
    etiquetas = [
        panel.layout().itemAt(i).widget()
        for i in range(panel.layout().count())
        if isinstance(panel.layout().itemAt(i).widget(), QLabel)
    ]
    assert any("no tiene firmas" in e.text().lower() for e in etiquetas)


def test_una_tarjeta_por_firma(qapp: object) -> None:
    panel = VerificationPanel()

    panel.mostrar((_resultado(EstadoFirma.VALIDA), _resultado(EstadoFirma.INVALIDA)))

    assert panel.tarjetas() == 2


def test_las_tarjetas_llevan_la_propiedad_sigstate(qapp: object) -> None:
    panel = VerificationPanel()

    panel.mostrar((_resultado(EstadoFirma.DESCONOCIDA),))
    tarjeta = _primer_frame(panel)

    assert tarjeta.property("sigCard") is True
    assert tarjeta.property("sigState") == "unknown"


def test_mostrar_reemplaza_las_tarjetas_previas(qapp: object) -> None:
    panel = VerificationPanel()

    panel.mostrar((_resultado(EstadoFirma.VALIDA), _resultado(EstadoFirma.VALIDA)))
    panel.mostrar((_resultado(EstadoFirma.INVALIDA),))

    assert panel.tarjetas() == 1
