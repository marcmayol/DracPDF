"""Fábrica de widgets Qt para cada tipo de campo de formulario.

En esta fase los widgets solo muestran el valor actual del campo. La conexión de
las señales de edición (para escribir en el documento) se añade en la tarea 3.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QListWidget,
    QRadioButton,
    QWidget,
)

from lectorpdf.core.domain.formularios import CampoFormulario, TipoCampo

_ESTADO_OFF = "Off"


#: Propiedad dinámica que marca los widgets del overlay para darles estilo fijo
#: de documento (papel) en el QSS, excluidos del tema de la app.
PROP_CAMPO = "documentoCampo"


def crear_widget(campo: CampoFormulario) -> QWidget:
    """Crea el widget Qt que representa `campo` con su valor actual."""
    widget = _crear(campo)
    # El overlay va sobre el papel del documento: no debe seguir el tema de la
    # app. Se marca para que el QSS le dé estilo de documento fijo.
    widget.setProperty(PROP_CAMPO, "true")
    if campo.solo_lectura:
        widget.setEnabled(False)
    return widget


def _crear(campo: CampoFormulario) -> QWidget:
    if campo.tipo == TipoCampo.TEXTO:
        return QLineEdit(campo.valor)
    if campo.tipo == TipoCampo.CASILLA:
        casilla = QCheckBox()
        casilla.setChecked(_marcado(campo))
        return casilla
    if campo.tipo == TipoCampo.RADIO:
        radio = QRadioButton()
        radio.setChecked(_marcado(campo))
        return radio
    if campo.tipo == TipoCampo.COMBO:
        combo = QComboBox()
        combo.addItems(campo.opciones)
        if campo.valor:
            combo.setCurrentText(campo.valor)
        return combo
    if campo.tipo == TipoCampo.LISTA:
        lista = QListWidget()
        lista.addItems(campo.opciones)
        for fila in range(lista.count()):
            item = lista.item(fila)
            if item is not None and item.text() == campo.valor:
                lista.setCurrentItem(item)
        return lista
    raise ValueError(f"Tipo de campo no soportado: {campo.tipo}")


def _marcado(campo: CampoFormulario) -> bool:
    return campo.estado_activado is not None and campo.valor == campo.estado_activado


def conectar_edicion(
    widget: QWidget, campo: CampoFormulario, al_editar: Callable[[str], None]
) -> None:
    """Conecta la señal de fin de edición del widget para propagar el nuevo valor.

    Texto: al perder el foco (`editingFinished`), no en cada tecla. Casilla/radio:
    al alternar. Combo/lista: al cambiar la selección (eventos discretos).
    """
    if campo.solo_lectura:
        return
    on = campo.estado_activado or ""

    if isinstance(widget, QLineEdit):
        widget.editingFinished.connect(lambda: al_editar(widget.text()))
    elif isinstance(widget, QCheckBox):
        widget.toggled.connect(
            lambda marcado: al_editar(on if marcado else _ESTADO_OFF)
        )
    elif isinstance(widget, QRadioButton):
        widget.toggled.connect(lambda marcado: al_editar(on) if marcado else None)
    elif isinstance(widget, QComboBox | QListWidget):
        widget.currentTextChanged.connect(al_editar)
