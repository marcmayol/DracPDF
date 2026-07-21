"""Generación del QSS desde los tokens y aplicación/persistencia del tema.

El QSS se renderiza desde una plantilla sustituyendo los tokens (colores, radios,
tipografía): ningún color aparece literal aquí. Se usa string.Template ($nombre)
porque no colisiona con las llaves { } de QSS.
"""

from __future__ import annotations

from string import Template

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from lectorpdf.ui.theme.tokens import (
    CAMPO_BORDE,
    CAMPO_FONDO,
    CAMPO_SELECCION,
    CAMPO_TEXTO,
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
/* "Firmar con certificado": acción destacada del grupo de firma (maqueta 5.1). */
QToolButton#botonFirmar { background: $accent_18; }
QToolButton#botonFirmar:hover { background: $accent_30; }

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

/* Ampliación (Fase 8): barra de menús, pestañas, árbol de outline, banda. */
QMenuBar { min-height: 28px; }
QMenu { min-width: 240px; }
QMenu::item:disabled { color: $text_muted; }
QMenu::indicator { width: 14px; height: 14px; margin-left: 6px; }
QTabBar { background: transparent; }
QTabBar::tab {
    background: transparent; color: $text_muted; padding: 7px 14px;
    border: none; border-bottom: 2px solid transparent; font-size: ${tam_meta}px;
}
QTabBar::tab:selected { color: $text; border-bottom: 2px solid $accent; }
QTabBar::tab:hover:!selected { color: $text; }
/* Panel del QTabWidget (docks Miniaturas/Índice): que el contenedor use la
   superficie del tema y no exponga la paleta por defecto en los bordes/franjas. */
QTabWidget::pane { border: none; background: $surface; }
QStackedWidget { background: $surface; }
QTreeView::item { height: 24px; border-radius: ${r_control}px; padding: 0 4px; }
QTreeView::item:hover { background: $surface_2; }
QTreeView::item:selected { background: $accent_30; color: $text; }
QTreeView::branch { background: transparent; }
/* Banda no modal "documento firmado" (propiedad infoBanner) */
QFrame[infoBanner="true"] {
    background: $banner_bg; border: none;
    border-bottom: 1px solid $banner_borde; min-height: 32px; max-height: 32px;
}
QFrame[infoBanner="true"] QLabel {
    color: $banner_text; font-size: ${tam_meta}px; background: transparent;
}
QFrame[infoBanner="true"] QPushButton {
    background: transparent; border: 1px solid $banner_borde;
    color: $banner_text; padding: 2px 10px; border-radius: ${r_control}px;
}

/* Overlay de formularios: estilo de documento FIJO (papel), idéntico en ambos
   temas. Los valores no dependen del tema (excluye estos widgets del chrome). */
QLineEdit[documentoCampo="true"],
QComboBox[documentoCampo="true"],
QListWidget[documentoCampo="true"] {
    background: $campo_fondo; color: $campo_texto;
    border: 1px solid $campo_borde; border-radius: ${r_control}px;
    selection-background-color: $campo_seleccion; selection-color: $campo_texto;
}
QLineEdit[documentoCampo="true"]:focus,
QComboBox[documentoCampo="true"]:focus,
QListWidget[documentoCampo="true"]:focus { border-color: $campo_seleccion; }
QCheckBox[documentoCampo="true"],
QRadioButton[documentoCampo="true"] { background: transparent; color: $campo_texto; }
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
        accent_18=rgba(tema.accent, 0.18),
        sig_valid=tema.sig_valid,
        sig_invalid=tema.sig_invalid,
        sig_unknown=tema.sig_unknown,
        familia_ui=_familia(TIPOGRAFIA.familia_ui),
        tam_base=TIPOGRAFIA.tam_base,
        tam_meta=TIPOGRAFIA.tam_meta,
        r_control=RADIOS.control,
        r_panel=RADIOS.panel,
        # Banda "documento firmado": ámbar derivado del token sig_unknown del tema.
        banner_bg=rgba(tema.sig_unknown, 0.10),
        banner_borde=rgba(tema.sig_unknown, 0.35),
        banner_text=tema.sig_unknown,
        # Campos del overlay: estilo de documento fijo, igual en ambos temas.
        campo_fondo=CAMPO_FONDO,
        campo_borde=CAMPO_BORDE,
        campo_texto=CAMPO_TEXTO,
        campo_seleccion=CAMPO_SELECCION,
    )


def paleta_desde_tema(tema: Tema) -> QPalette:
    """Paleta Qt derivada de los tokens del tema.

    Complementa al QSS: cubre lo que el QSS no estiliza (diálogos nativos,
    QMessageBox, roles de sistema) para que el modo oscuro del SO no se cuele con
    superficies o textos ajenos al tema. El QSS sigue teniendo prioridad sobre los
    widgets que sí estiliza."""
    p = QPalette()
    rol = QPalette.ColorRole
    p.setColor(rol.Window, QColor(tema.bg))
    p.setColor(rol.WindowText, QColor(tema.text))
    p.setColor(rol.Base, QColor(tema.canvas))
    p.setColor(rol.AlternateBase, QColor(tema.surface_2))
    p.setColor(rol.Text, QColor(tema.text))
    p.setColor(rol.Button, QColor(tema.surface_2))
    p.setColor(rol.ButtonText, QColor(tema.text))
    p.setColor(rol.ToolTipBase, QColor(tema.surface_2))
    p.setColor(rol.ToolTipText, QColor(tema.text))
    p.setColor(rol.PlaceholderText, QColor(tema.text_muted))
    p.setColor(rol.Highlight, QColor(tema.accent))
    p.setColor(rol.HighlightedText, QColor(tema.on_accent))
    p.setColor(rol.Link, QColor(tema.accent))
    deshabilitado = QPalette.ColorGroup.Disabled
    for r in (rol.WindowText, rol.Text, rol.ButtonText):
        p.setColor(deshabilitado, r, QColor(tema.text_muted))
    return p


def aplicar_tema(app: QApplication, tema: Tema) -> None:
    app.setStyleSheet(generar_qss(tema))
    app.setPalette(paleta_desde_tema(tema))


def guardar_preferencia_tema(nombre: str) -> None:
    QSettings(_ORG, _APP).setValue(_CLAVE_TEMA, nombre)


def cargar_tema_preferido() -> Tema:
    nombre = QSettings(_ORG, _APP).value(_CLAVE_TEMA, TEMA_POR_DEFECTO.nombre)
    return tema_por_nombre(str(nombre))
