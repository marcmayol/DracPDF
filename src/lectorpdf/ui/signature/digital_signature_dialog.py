"""Diálogo para reunir la credencial y los parámetros de la firma digital."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lectorpdf.core.domain.firma_digital import CredencialPKCS12


class DigitalSignatureDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Firmar digitalmente")

        self._ruta_p12 = QLineEdit()
        self._ruta_p12.setReadOnly(True)
        elegir = QPushButton("Elegir…")
        elegir.clicked.connect(self._elegir_p12)
        self._contrasena = QLineEdit()
        self._contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self._razon = QLineEdit()
        self._visible = QCheckBox("Colocar un sello visible en la página")
        self._visible.setChecked(True)

        form = QFormLayout()
        form.addRow("Certificado (.p12/.pfx):", self._ruta_p12)
        form.addRow("", elegir)
        form.addRow("Contraseña:", self._contrasena)
        form.addRow("Razón:", self._razon)
        form.addRow("", self._visible)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._aceptar)
        botones.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(botones)

    def _elegir_p12(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Certificado PKCS#12", "", "Certificados (*.p12 *.pfx)"
        )
        if ruta:
            self._ruta_p12.setText(ruta)

    def _aceptar(self) -> None:
        if self._ruta_p12.text():
            self.accept()

    def credencial(self) -> CredencialPKCS12 | None:
        if not self._ruta_p12.text():
            return None
        return CredencialPKCS12(Path(self._ruta_p12.text()), self._contrasena.text())

    def razon(self) -> str | None:
        return self._razon.text() or None

    def sello_visible(self) -> bool:
        return self._visible.isChecked()
