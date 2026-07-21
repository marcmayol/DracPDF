"""Tests de humo de las cuatro pantallas clave con ambos temas aplicados.

Verifica que aplicar el tema (QSS) no rompe ninguna pantalla ni el overlay de
formularios ni el canvas de firma.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from lectorpdf.core.domain.firma_digital import EstadoFirma, ResultadoVerificacion
from lectorpdf.ui.about_dialog import AboutDialog
from lectorpdf.ui.main_window import MainWindow
from lectorpdf.ui.signature.signature_canvas import SignatureCanvas
from lectorpdf.ui.signature.signature_dialog import SignatureDialog
from lectorpdf.ui.signature.verification_panel import VerificationPanel
from lectorpdf.ui.theme import tokens
from lectorpdf.ui.theme.estilos import aplicar_tema, guardar_preferencia_tema
from tests.adapters.generar_fixtures_formularios import generar_formulario_completo

_TEMAS = [tokens.TEMA_OSCURO, tokens.TEMA_CLARO]


def _app() -> QApplication:
    app = QApplication.instance()
    assert isinstance(app, QApplication)
    return app


@pytest.mark.parametrize("tema", _TEMAS)
def test_vista_principal_arranca_con_el_tema(qapp: object, tema: tokens.Tema) -> None:
    guardar_preferencia_tema(tema.nombre)  # la ventana aplica su propio tema

    ventana = MainWindow()
    ventana.resize(1000, 700)
    ventana.show()

    # El área central es el QTabWidget de vistas; el visor pertenece a la ventana.
    assert ventana.centralWidget() is ventana._pestanas
    assert ventana._visor.window() is ventana
    assert ventana._tema is tema
    assert tema.bg in _app().styleSheet()
    assert ventana._visor.backgroundBrush().color().name() == tema.canvas.lower()


def _color_viewport_miniaturas(ventana: MainWindow) -> str:
    """Color de fondo efectivo del viewport del panel de miniaturas (esquina
    superior izquierda, sin miniaturas encima)."""
    _app().processEvents()
    img = ventana._miniaturas.viewport().grab().toImage()
    return img.pixelColor(2, 2).name()


@pytest.mark.parametrize("tema", _TEMAS)
def test_viewport_miniaturas_usa_superficie_del_tema(
    qapp: object, tema: tokens.Tema
) -> None:
    guardar_preferencia_tema(tema.nombre)
    ventana = MainWindow()
    ventana.resize(1000, 700)
    ventana.show()

    # El viewport del panel de miniaturas usa la superficie del tema activo
    # (no la paleta por defecto ni el tema contrario) ya al arrancar.
    assert _color_viewport_miniaturas(ventana) == tema.surface.lower()


def test_viewport_miniaturas_se_repinta_al_cambiar_tema_en_caliente(
    qapp: object,
) -> None:
    guardar_preferencia_tema(tokens.TEMA_OSCURO.nombre)
    ventana = MainWindow()
    ventana.resize(1000, 700)
    ventana.show()
    assert _color_viewport_miniaturas(ventana) == tokens.TEMA_OSCURO.surface.lower()

    # Cambio en caliente: el restyle debe propagarse también al viewport.
    ventana._aplicar_tema(tokens.TEMA_CLARO)
    assert _color_viewport_miniaturas(ventana) == tokens.TEMA_CLARO.surface.lower()

    ventana._aplicar_tema(tokens.TEMA_OSCURO)
    assert _color_viewport_miniaturas(ventana) == tokens.TEMA_OSCURO.surface.lower()


@pytest.mark.parametrize("tema", _TEMAS)
def test_modo_formulario_sobrevive_al_tema(
    qapp: object, tmp_path: Path, tema: tokens.Tema
) -> None:
    guardar_preferencia_tema(tema.nombre)
    ventana = MainWindow()
    ventana.resize(1000, 700)
    ventana.show()

    ventana.abrir_ruta(generar_formulario_completo(tmp_path / "f.pdf"))

    # El overlay de formularios sigue teniendo proxies tras aplicar el tema.
    assert ventana._capa_form.proxies()


@pytest.mark.parametrize("tema", _TEMAS)
def test_dialogo_firma_dibujada_con_tema(qapp: object, tema: tokens.Tema) -> None:
    aplicar_tema(_app(), tema)

    dialogo = SignatureDialog()

    # El canvas de firma se construye y sigue vacío (no lo rompe el QSS).
    canvas = dialogo.findChild(SignatureCanvas)
    assert canvas is not None
    assert canvas.esta_vacio() is True


@pytest.mark.parametrize("tema", _TEMAS)
def test_panel_verificacion_tres_estados_con_tema(
    qapp: object, tema: tokens.Tema
) -> None:
    aplicar_tema(_app(), tema)
    panel = VerificationPanel()

    resultados = tuple(
        ResultadoVerificacion(
            firmante="Ana",
            estado=estado,
            cubre_todo_el_documento=estado == EstadoFirma.VALIDA,
            sellada_en_tiempo=False,
            motivo="motivo",
        )
        for estado in (EstadoFirma.VALIDA, EstadoFirma.INVALIDA, EstadoFirma.DESCONOCIDA)
    )
    panel.mostrar(resultados)

    assert panel.tarjetas() == 3


@pytest.mark.parametrize("tema", _TEMAS)
def test_about_con_tema(qapp: object, tema: tokens.Tema) -> None:
    aplicar_tema(_app(), tema)

    dialogo = AboutDialog(es_oscuro=tema.es_oscuro)

    assert "DracPDF" in dialogo.windowTitle()
