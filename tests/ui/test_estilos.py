"""Tests de la generación de QSS desde tokens y de la persistencia de tema."""

from __future__ import annotations

import re

from PySide6.QtWidgets import QApplication

from lectorpdf.ui.theme import tokens
from lectorpdf.ui.theme.estilos import (
    aplicar_tema,
    cargar_tema_preferido,
    generar_qss,
    guardar_preferencia_tema,
)


def test_qss_no_deja_marcadores_sin_sustituir() -> None:
    qss = generar_qss(tokens.TEMA_OSCURO)
    assert "$" not in qss


def test_qss_usa_los_colores_del_tema() -> None:
    oscuro = generar_qss(tokens.TEMA_OSCURO)
    claro = generar_qss(tokens.TEMA_CLARO)

    assert tokens.TEMA_OSCURO.accent in oscuro  # #E0534A
    assert tokens.TEMA_OSCURO.accent not in claro
    assert tokens.TEMA_CLARO.bg in claro  # #F2F2F5
    # El tinte de selección se deriva del acento.
    assert tokens.rgba(tokens.TEMA_OSCURO.accent, 0.30) in oscuro


def test_qss_incluye_los_estados_de_firma_semanticos() -> None:
    qss = generar_qss(tokens.TEMA_OSCURO)
    assert tokens.TEMA_OSCURO.sig_valid in qss
    assert tokens.TEMA_OSCURO.sig_invalid in qss
    assert tokens.TEMA_OSCURO.sig_unknown in qss


def test_qss_no_contiene_hex_ajenos_a_los_tokens() -> None:
    qss = generar_qss(tokens.TEMA_OSCURO)
    hex_en_qss = set(re.findall(r"#[0-9A-Fa-f]{6}", qss))
    permitidos = {
        getattr(tokens.TEMA_OSCURO, c)
        for c in vars(tokens.TEMA_OSCURO)
        if isinstance(getattr(tokens.TEMA_OSCURO, c), str)
        and getattr(tokens.TEMA_OSCURO, c).startswith("#")
    }
    assert hex_en_qss <= permitidos


def test_aplicar_tema_pone_el_stylesheet(qapp: object) -> None:
    app = QApplication.instance()
    assert isinstance(app, QApplication)

    aplicar_tema(app, tokens.TEMA_CLARO)

    assert tokens.TEMA_CLARO.bg in app.styleSheet()
    aplicar_tema(app, tokens.TEMA_OSCURO)  # restaurar


def test_qss_incluye_los_componentes_nuevos_de_fase_8() -> None:
    qss = generar_qss(tokens.TEMA_OSCURO)
    assert "min-height: 28px" in qss  # QMenuBar
    assert "QTabBar::tab" in qss  # pestañas Miniaturas | Índice
    assert "QTreeView::item" in qss  # árbol de outline
    assert "QFrame[infoBanner=" in qss  # banda documento firmado


def test_banner_deriva_del_token_sig_unknown_por_tema() -> None:
    oscuro = generar_qss(tokens.TEMA_OSCURO)
    claro = generar_qss(tokens.TEMA_CLARO)
    assert tokens.rgba(tokens.TEMA_OSCURO.sig_unknown, 0.35) in oscuro
    assert tokens.rgba(tokens.TEMA_CLARO.sig_unknown, 0.35) in claro
    assert tokens.TEMA_OSCURO.sig_unknown in oscuro  # banner-text


def test_persistencia_del_tema(qapp: object) -> None:
    guardar_preferencia_tema("claro")
    assert cargar_tema_preferido() is tokens.TEMA_CLARO

    guardar_preferencia_tema("oscuro")  # restaurar por defecto
    assert cargar_tema_preferido() is tokens.TEMA_OSCURO
