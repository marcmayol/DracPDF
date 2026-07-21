"""Test de humo: cada diálogo de la app en ambos temas, fondo y texto coherentes.

Verifica que, con el tema aplicado a nivel de QApplication, cualquier diálogo
hereda la paleta del tema (fondo y texto del MISMO tema), de modo que no quedan
etiquetas oscuras sobre superficie oscura (o viceversa) en ningún tema.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QDialog

from lectorpdf.core.domain.contenido import PropiedadesDocumento
from lectorpdf.ui.about_dialog import AboutDialog
from lectorpdf.ui.herramientas.dividir_dialog import DividirDialog
from lectorpdf.ui.herramientas.unir_dialog import UnirDialog
from lectorpdf.ui.propiedades_dialog import PropiedadesDialog
from lectorpdf.ui.signature.digital_signature_dialog import DigitalSignatureDialog
from lectorpdf.ui.signature.signature_dialog import SignatureDialog
from lectorpdf.ui.theme import tokens
from lectorpdf.ui.theme.estilos import aplicar_tema


def _props() -> PropiedadesDocumento:
    return PropiedadesDocumento(
        titulo="T",
        autor="A",
        asunto="",
        palabras_clave="",
        creador="",
        productor="",
        version_pdf="PDF 1.7",
        cifrado=False,
        num_paginas=1,
        tamano_bytes=10,
    )


def _crear_dialogos(tema: tokens.Tema) -> list[QDialog]:
    return [
        AboutDialog(tema.es_oscuro),
        DividirDialog(),
        UnirDialog(),
        SignatureDialog(),
        DigitalSignatureDialog(),
        PropiedadesDialog(_props(), Path("C:/docs/x.pdf")),
    ]


@pytest.mark.parametrize("tema", [tokens.TEMA_OSCURO, tokens.TEMA_CLARO])
def test_cada_dialogo_hereda_el_tema(qapp: object, tema: tokens.Tema) -> None:
    app = QApplication.instance()
    assert isinstance(app, QApplication)
    aplicar_tema(app, tema)

    for dialogo in _crear_dialogos(tema):
        paleta = dialogo.palette()
        fondo = paleta.color(QPalette.ColorRole.Window)
        texto = paleta.color(QPalette.ColorRole.WindowText)
        nombre = type(dialogo).__name__
        assert fondo == QColor(tema.bg), f"{nombre}: fondo {fondo.name()} != {tema.bg}"
        assert texto == QColor(tema.text), f"{nombre}: texto {texto.name()} != {tema.text}"
        # Fondo y texto tienen contraste (no es el mismo color): legible.
        assert fondo != texto
