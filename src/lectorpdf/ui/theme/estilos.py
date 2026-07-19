"""Generación del QSS desde los tokens y aplicación/persistencia del tema.

El QSS se renderiza desde una plantilla sustituyendo los tokens (colores, radios,
tipografía): ningún color aparece literal aquí. Se usa string.Template ($nombre)
porque no colisiona con las llaves { } de QSS.
"""

from __future__ import annotations

from string import Template

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from lectorpdf.ui.theme.tokens import (
    RADIOS,
    TEMA_POR_DEFECTO,
    TIPOGRAFIA,
    Tema,
    rgba,
    tema_por_nombre,
)

_ORG = "lectorpdf"
_APP = "lectorpdf"
_CLAVE_TEMA = "ui/tema"

_PLANTILLA = Template(
    """
QMainWindow, QDialog, QWidget#centralWidget {
    background: $bg;
    color: $text;
    font-family: $familia_ui;
    font-size: ${tam_base}px;
}
QGraphicsView { background: $canvas; border: none; }

QToolBar {
    background: $surface;
    border: none;
    border-bottom: 1px solid $border;
    padding: 4px 8px;
    spacing: 2px;
}
QToolBar::separator { background: $border; width: 1px; margin: 6px 6px; }
QToolButton {
    background: transparent; border: none; border-radius: ${r_control}px;
    padding: 5px; color: $text;
}
QToolButton:hover { background: $surface_2; }
QToolButton:pressed { background: $border; }
QToolButton:checked { background: $accent_30; color: $accent; }
QToolButton:disabled { color: $text_muted; }

QPushButton {
    background: $surface_2; color: $text;
    border: 1px solid $border; border-radius: ${r_control}px;
    padding: 5px 14px; min-height: 18px;
}
QPushButton:hover { background: $border; }
QPushButton:default, QPushButton[primary="true"] {
    background: $accent; color: $on_accent; border: none; font-weight: 600;
}
QPushButton:default:hover, QPushButton[primary="true"]:hover { background: $accent_hover; }
QPushButton:disabled { color: $text_muted; background: $surface; }

QLineEdit, QSpinBox, QComboBox {
    background: $canvas; color: $text;
    border: 1px solid $border; border-radius: ${r_control}px;
    padding: 4px 8px; selection-background-color: $accent_30;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: $accent; }

QListView, QTreeView {
    background: $surface; color: $text;
    border: none; outline: none;
}
QListView::item { border-radius: ${r_control}px; padding: 4px; }
QListView::item:hover { background: $surface_2; }
QListView::item:selected { background: $accent_30; color: $text; }

QMenuBar { background: $bg; color: $text; }
QMenuBar::item { padding: 4px 10px; border-radius: ${r_control}px; }
QMenuBar::item:selected { background: $surface_2; }
QMenu {
    background: $surface; color: $text;
    border: 1px solid $border; border-radius: ${r_panel}px; padding: 4px;
}
QMenu::item { padding: 5px 24px 5px 12px; border-radius: ${r_control}px; }
QMenu::item:selected { background: $surface_2; }
QMenu::separator { height: 1px; background: $border; margin: 4px 8px; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: $border; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: $text_muted; }
QScrollBar:horizontal { background: transparent; height: 10px; }
QScrollBar::handle:horizontal { background: $border; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QDockWidget { color: $text; titlebar-close-icon: none; }
QDockWidget::title { background: $surface; padding: 4px 8px; }

QStatusBar {
    background: $surface; color: $text_muted;
    border-top: 1px solid $border; font-size: ${tam_meta}px;
}
QToolTip {
    background: $surface_2; color: $text;
    border: 1px solid $border; border-radius: ${r_control}px; padding: 4px 8px;
}

/* Estados de firma — propiedad dinámica sigState (tokens semánticos del diseño) */
QLabel[sigState="valid"]   { color: $sig_valid;   font-weight: 600; }
QLabel[sigState="invalid"] { color: $sig_invalid; font-weight: 600; }
QLabel[sigState="unknown"] { color: $sig_unknown; font-weight: 600; }
QFrame[sigCard="true"] {
    background: $surface; border: 1px solid $border; border-radius: ${r_panel}px;
}
QFrame[sigCard="true"][sigState="valid"]   { border-left: 3px solid $sig_valid; }
QFrame[sigCard="true"][sigState="invalid"] { border-left: 3px solid $sig_invalid; }
QFrame[sigCard="true"][sigState="unknown"] { border-left: 3px solid $sig_unknown; }
"""
)


def _familia(familias: tuple[str, ...]) -> str:
    return ", ".join(f'"{f}"' for f in familias)


def generar_qss(tema: Tema) -> str:
    """Renderiza la hoja de estilos QSS del tema a partir de los tokens."""
    return _PLANTILLA.substitute(
        canvas=tema.canvas,
        bg=tema.bg,
        surface=tema.surface,
        surface_2=tema.surface_2,
        border=tema.border,
        text=tema.text,
        text_muted=tema.text_muted,
        accent=tema.accent,
        accent_hover=tema.accent_hover,
        on_accent=tema.on_accent,
        accent_30=rgba(tema.accent, 0.30),
        sig_valid=tema.sig_valid,
        sig_invalid=tema.sig_invalid,
        sig_unknown=tema.sig_unknown,
        familia_ui=_familia(TIPOGRAFIA.familia_ui),
        tam_base=TIPOGRAFIA.tam_base,
        tam_meta=TIPOGRAFIA.tam_meta,
        r_control=RADIOS.control,
        r_panel=RADIOS.panel,
    )


def aplicar_tema(app: QApplication, tema: Tema) -> None:
    app.setStyleSheet(generar_qss(tema))


def guardar_preferencia_tema(nombre: str) -> None:
    QSettings(_ORG, _APP).setValue(_CLAVE_TEMA, nombre)


def cargar_tema_preferido() -> Tema:
    nombre = QSettings(_ORG, _APP).value(_CLAVE_TEMA, TEMA_POR_DEFECTO.nombre)
    return tema_por_nombre(str(nombre))
