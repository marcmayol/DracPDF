"""Sincroniza la barra de título nativa de Windows con el tema activo.

Usa DWMWA_USE_IMMERSIVE_DARK_MODE para que el marco de la ventana (barra de
título, botones) siga el tema claro/oscuro de la app. No-op fuera de Windows.
Un gestor instalado como filtro de eventos de la QApplication lo aplica a toda
ventana de nivel superior al mostrarse (ventana principal, diálogos, mensajes).
"""

from __future__ import annotations

import ctypes
import sys

from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

# Atributo DWM: 20 en Windows 10 2004+, 19 en compilaciones anteriores.
_DWMWA_NUEVO = 20
_DWMWA_ANTIGUO = 19


def aplicar_modo_oscuro(widget: QWidget, oscuro: bool) -> None:
    """Aplica (o quita) el modo oscuro a la barra de título de `widget`. No-op
    fuera de Windows; los errores del DWM (p. ej. handle inválido) se ignoran."""
    if sys.platform != "win32":
        return
    app = QGuiApplication.instance()
    if isinstance(app, QGuiApplication) and app.platformName() == "offscreen":
        return  # sin display real (tests): no forzar winId() ni llamar al DWM
    try:
        hwnd = int(widget.winId())
        valor = ctypes.c_int(1 if oscuro else 0)
        dwm = ctypes.windll.dwmapi
        for atributo in (_DWMWA_NUEVO, _DWMWA_ANTIGUO):
            dwm.DwmSetWindowAttribute(
                hwnd, atributo, ctypes.byref(valor), ctypes.sizeof(valor)
            )
    except Exception:  # pragma: no cover - depende del SO/compilación
        pass


class GestorBarraTitulo(QObject):
    """Aplica el modo oscuro de la barra de título a cada ventana al mostrarse."""

    def __init__(self, oscuro: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._oscuro = oscuro

    def set_oscuro(self, oscuro: bool) -> None:
        self._oscuro = oscuro

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Show
            and isinstance(obj, QWidget)
            and obj.isWindow()
        ):
            aplicar_modo_oscuro(obj, self._oscuro)
        return False


def instalar_gestor(app: QGuiApplication, oscuro: bool) -> GestorBarraTitulo:
    """Devuelve el gestor único de la app (uno por QApplication), instalándolo
    como filtro de eventos la primera vez. Evita acumular filtros al crear varias
    ventanas (p. ej. en los tests, que comparten una QApplication de sesión)."""
    gestor = app.findChild(GestorBarraTitulo)
    if gestor is None:
        gestor = GestorBarraTitulo(oscuro, app)
        app.installEventFilter(gestor)
    else:
        gestor.set_oscuro(oscuro)
    return gestor
