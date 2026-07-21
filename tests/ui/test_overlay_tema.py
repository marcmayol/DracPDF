"""Verifica que un campo de formulario RELLENO se ve igual en ambos temas.

Consecuencia del punto 2 (el overlay usa estilo de documento fijo): con el QSS y
la paleta del tema aplicados a la app, un campo relleno se renderiza idéntico en
tema claro y oscuro.
"""

from __future__ import annotations

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QLineEdit

from lectorpdf.core.domain.formularios import CampoFormulario, RectanguloPt, TipoCampo
from lectorpdf.ui.forms.widgets_campo import crear_widget
from lectorpdf.ui.theme import tokens
from lectorpdf.ui.theme.estilos import aplicar_tema


def _campo_relleno() -> CampoFormulario:
    return CampoFormulario(
        id="0:0",
        nombre="nombre",
        tipo=TipoCampo.TEXTO,
        pagina=0,
        rect_pt=RectanguloPt(0, 0, 200, 24),
        valor="Marc Mayol",
    )


def _render_campo(tema: tokens.Tema) -> QImage:
    app = QApplication.instance()
    assert isinstance(app, QApplication)
    aplicar_tema(app, tema)  # QSS + paleta del tema a nivel de app
    widget = crear_widget(_campo_relleno())
    assert isinstance(widget, QLineEdit)
    widget.resize(200, 28)
    widget.ensurePolished()
    return widget.grab().toImage()


def test_campo_relleno_identico_en_ambos_temas(qapp: object) -> None:
    en_oscuro = _render_campo(tokens.TEMA_OSCURO)
    en_claro = _render_campo(tokens.TEMA_CLARO)

    assert not en_oscuro.isNull() and not en_claro.isNull()
    assert en_oscuro.size() == en_claro.size()
    # El campo (fondo, borde, texto) se pinta igual: renderizado idéntico.
    assert en_oscuro == en_claro
