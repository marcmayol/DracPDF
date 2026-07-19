"""Punto de entrada del ejecutable DracPDF (para PyInstaller)."""

from __future__ import annotations

import sys

from lectorpdf.ui.app import main

if __name__ == "__main__":
    sys.exit(main())
