"""Punto de entrada de la aplicación de escritorio."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QTranslator
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from lectorpdf.ui.instancia_unica import InstanciaUnica, nombre_servidor
from lectorpdf.ui.main_window import MainWindow
from lectorpdf.ui.theme.estilos import (
    AJUSTES_APP,
    AJUSTES_ORG,
    aplicar_tema,
    cargar_tema_preferido,
)
from lectorpdf.ui.theme.marca import NOMBRE_APP, ruta_icono_app


def cargar_traducciones(app: QApplication) -> list[QTranslator]:
    """Instala las traducciones estándar de Qt en español (OK/Cancel/Close…).

    Devuelve los traductores instalados (parentados a la app para mantenerlos
    vivos); lista vacía si los .qm no están disponibles."""
    ruta = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    traductores: list[QTranslator] = []
    for nombre in ("qtbase_es", "qt_es"):
        traductor = QTranslator(app)
        if traductor.load(nombre, ruta):
            app.installTranslator(traductor)
            traductores.append(traductor)
    return traductores


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)
    # Identidad para QSettings fijada ANTES de cualquier lectura de ajustes e
    # idéntica en desarrollo y en el .exe: todas las preferencias (tema, sesión,
    # recientes, vista) usan siempre el mismo almacén. Las claves emplean además
    # QSettings(AJUSTES_ORG, AJUSTES_APP) explícito con estos mismos valores.
    app.setOrganizationName(AJUSTES_ORG)
    app.setApplicationName(AJUSTES_APP)
    app.setApplicationDisplayName(NOMBRE_APP)
    cargar_traducciones(app)  # OK/Cancel/Close… en español

    # Instancia única: si ya hay una corriendo, le pasamos el documento y salimos.
    ruta_arg = argv[1] if len(argv) > 1 else ""
    instancia = InstanciaUnica(nombre_servidor(), app)
    if instancia.ya_hay_instancia(ruta_arg):
        return 0
    instancia.iniciar_servidor()

    icono_app = ruta_icono_app()
    if icono_app is not None:
        app.setWindowIcon(QIcon(str(icono_app)))
    aplicar_tema(app, cargar_tema_preferido())

    # Arranque con fichero (doble clic / asociación / CLI): se abre solo ese
    # documento, sin restaurar ni sobrescribir la sesión de trabajo guardada.
    # Arranque normal (sin fichero): se restaura la sesión anterior (si está
    # activado) y se persiste al cerrar.
    con_fichero = bool(ruta_arg)
    ventana = MainWindow(
        restaurar_sesion=not con_fichero,
        persistir_sesion=not con_fichero,
    )
    instancia.mensaje_recibido.connect(ventana.abrir_desde_instancia)
    ventana.show()

    if ruta_arg:
        ventana.abrir_ruta_con_aviso(Path(ruta_arg))

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
