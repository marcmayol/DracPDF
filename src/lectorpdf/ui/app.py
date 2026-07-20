"""Punto de entrada de la aplicación de escritorio."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from lectorpdf.ui.instancia_unica import InstanciaUnica, nombre_servidor
from lectorpdf.ui.main_window import MainWindow
from lectorpdf.ui.theme.estilos import aplicar_tema, cargar_tema_preferido
from lectorpdf.ui.theme.marca import NOMBRE_APP, ruta_icono_app


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)
    app.setApplicationName(NOMBRE_APP)
    app.setApplicationDisplayName(NOMBRE_APP)

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

    # Restaura la sesión anterior al arrancar (si el usuario lo tiene activado).
    ventana = MainWindow(restaurar_sesion=True)
    instancia.mensaje_recibido.connect(ventana.abrir_desde_instancia)
    ventana.show()

    # Permite abrir un PDF pasándolo como argumento: `lectorpdf documento.pdf`.
    if ruta_arg:
        ventana.abrir_ruta_con_aviso(Path(ruta_arg))

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
