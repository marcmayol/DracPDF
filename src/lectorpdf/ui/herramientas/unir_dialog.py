"""Diálogo para elegir y ordenar los PDF a unir."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class UnirDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, ruta_inicial: Path | None = None):
        super().__init__(parent)
        self.setWindowTitle("Unir PDF")
        self.resize(460, 320)

        self._lista = QListWidget()
        if ruta_inicial is not None:
            self._lista.addItem(str(ruta_inicial))

        anadir = QPushButton("Añadir…")
        quitar = QPushButton("Quitar")
        subir = QPushButton("Subir")
        bajar = QPushButton("Bajar")
        anadir.clicked.connect(self._anadir)
        quitar.clicked.connect(self._quitar)
        subir.clicked.connect(lambda: self._mover(-1))
        bajar.clicked.connect(lambda: self._mover(1))

        columna_botones = QVBoxLayout()
        for boton in (anadir, quitar, subir, bajar):
            columna_botones.addWidget(boton)
        columna_botones.addStretch(1)

        fila = QHBoxLayout()
        fila.addWidget(self._lista)
        fila.addLayout(columna_botones)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("PDF a unir (en este orden):"))
        layout.addLayout(fila)
        layout.addWidget(botones)

    def rutas(self) -> list[Path]:
        return [Path(self._lista.item(i).text()) for i in range(self._lista.count())]

    # -- Interno ------------------------------------------------------------

    def _anadir(self) -> None:
        ficheros, _ = QFileDialog.getOpenFileNames(
            self, "Añadir PDF", "", "Documentos PDF (*.pdf)"
        )
        for fichero in ficheros:
            self._lista.addItem(fichero)

    def _quitar(self) -> None:
        fila = self._lista.currentRow()
        if fila >= 0:
            self._lista.takeItem(fila)

    def _mover(self, delta: int) -> None:
        fila = self._lista.currentRow()
        nueva = fila + delta
        if fila < 0 or nueva < 0 or nueva >= self._lista.count():
            return
        item = self._lista.takeItem(fila)
        self._lista.insertItem(nueva, item)
        self._lista.setCurrentRow(nueva)
