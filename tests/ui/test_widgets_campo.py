"""Tests de la fábrica de widgets por tipo de campo."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QListWidget,
    QRadioButton,
)

from lectorpdf.core.domain.formularios import (
    CampoFormulario,
    RectanguloPt,
    TipoCampo,
)
from lectorpdf.ui.forms.widgets_campo import crear_widget

_RECT = RectanguloPt(0, 0, 100, 20)


def _campo(tipo: TipoCampo, **kw: object) -> CampoFormulario:
    base: dict[str, object] = dict(
        id="0:0", nombre="c", tipo=tipo, pagina=0, rect_pt=_RECT, valor=""
    )
    base.update(kw)
    return CampoFormulario(**base)  # type: ignore[arg-type]


def test_texto_muestra_su_valor(qapp: object) -> None:
    widget = crear_widget(_campo(TipoCampo.TEXTO, valor="Marc"))

    assert isinstance(widget, QLineEdit)
    assert widget.text() == "Marc"


def test_casilla_marcada_si_valor_igual_al_estado_on(qapp: object) -> None:
    marcada = crear_widget(
        _campo(TipoCampo.CASILLA, valor="Yes", estado_activado="Yes")
    )
    sin_marcar = crear_widget(
        _campo(TipoCampo.CASILLA, valor="Off", estado_activado="Yes")
    )

    assert isinstance(marcada, QCheckBox) and marcada.isChecked()
    assert isinstance(sin_marcar, QCheckBox) and not sin_marcar.isChecked()


def test_combo_carga_opciones_y_selecciona_valor(qapp: object) -> None:
    widget = crear_widget(
        _campo(TipoCampo.COMBO, valor="FR", opciones=("ES", "FR", "IT"))
    )

    assert isinstance(widget, QComboBox)
    assert widget.count() == 3
    assert widget.currentText() == "FR"


def test_lista_selecciona_el_valor_actual(qapp: object) -> None:
    widget = crear_widget(
        _campo(TipoCampo.LISTA, valor="verde", opciones=("rojo", "verde", "azul"))
    )

    assert isinstance(widget, QListWidget)
    item = widget.currentItem()
    assert item is not None and item.text() == "verde"


def test_radio_marcado_segun_estado(qapp: object) -> None:
    widget = crear_widget(
        _campo(TipoCampo.RADIO, valor="Yes", estado_activado="Yes")
    )

    assert isinstance(widget, QRadioButton) and widget.isChecked()


def test_campo_solo_lectura_queda_deshabilitado(qapp: object) -> None:
    widget = crear_widget(_campo(TipoCampo.TEXTO, valor="x", solo_lectura=True))

    assert not widget.isEnabled()
