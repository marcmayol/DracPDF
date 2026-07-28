"""Tests del diálogo de tablas: recuento previo, cambio de estrategia y aviso."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtWidgets import QDialogButtonBox

from lectorpdf.core.domain.tablas import (
    EstrategiaTablas,
    FormatoTabla,
    TablaDetectada,
)
from lectorpdf.ui.conversion.tablas_dialog import ConversionTablasDialog


def _detector(
    por_estrategia: dict[EstrategiaTablas, Sequence[TablaDetectada]],
) -> object:
    llamadas: list[EstrategiaTablas] = []

    def detectar(estrategia: EstrategiaTablas) -> Sequence[TablaDetectada]:
        llamadas.append(estrategia)
        return por_estrategia.get(estrategia, ())

    detectar.llamadas = llamadas  # type: ignore[attr-defined]
    return detectar


def test_muestra_lo_encontrado_antes_de_convertir(qapp: object) -> None:
    tablas = (TablaDetectada(0, 0, 3, 4), TablaDetectada(2, 0, 10, 2))
    detectar = _detector({EstrategiaTablas.LINEAS: tablas})

    dialogo = ConversionTablasDialog(detectar)  # type: ignore[arg-type]

    assert dialogo.detectadas() == tablas
    assert dialogo._lista.count() == 2
    assert dialogo._lista.item(0).text() == "Página 1, tabla 1: 3 filas × 4 columnas"
    assert "2 tabla(s) en 2 página(s)" in dialogo._resumen.text()


def test_sin_tablas_no_deja_convertir_y_sugiere_la_otra_estrategia(
    qapp: object,
) -> None:
    dialogo = ConversionTablasDialog(_detector({}))  # type: ignore[arg-type]

    boton = dialogo._botones.button(QDialogButtonBox.StandardButton.Ok)
    assert boton is not None and not boton.isEnabled()
    assert "No se ha encontrado ninguna tabla" in dialogo._resumen.text()
    assert "alineación del texto" in dialogo._resumen.text()


def test_cambiar_de_estrategia_vuelve_a_buscar_y_avisa(qapp: object) -> None:
    detectar = _detector(
        {EstrategiaTablas.TEXTO: (TablaDetectada(0, 0, 60, 4),)}
    )
    dialogo = ConversionTablasDialog(detectar)  # type: ignore[arg-type]
    assert dialogo.detectadas() == ()  # con líneas no hay nada

    dialogo._estrategia.setCurrentIndex(1)  # deducir por alineación

    assert dialogo.estrategia() is EstrategiaTablas.TEXTO
    assert len(dialogo.detectadas()) == 1
    assert "puede trocear en celdas párrafos que no son tablas" in (
        dialogo._resumen.text()
    )
    boton = dialogo._botones.button(QDialogButtonBox.StandardButton.Ok)
    assert boton is not None and boton.isEnabled()


def test_el_formato_por_defecto_es_csv(qapp: object) -> None:
    dialogo = ConversionTablasDialog(
        _detector({EstrategiaTablas.LINEAS: (TablaDetectada(0, 0, 2, 2),)})  # type: ignore[arg-type]
    )

    assert dialogo.formato() is FormatoTabla.CSV

    dialogo._formato.setCurrentIndex(1)

    assert dialogo.formato() is FormatoTabla.XLSX
