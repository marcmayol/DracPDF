"""Punto de entrada de la aplicación de escritorio."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from lectorpdf.ui.main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)

    ventana = MainWindow()
    ventana.show()

    # Permite abrir un PDF pasándolo como argumento: `lectorpdf documento.pdf`.
    if len(argv) > 1:
        ventana.abrir_ruta(Path(argv[1]))

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
