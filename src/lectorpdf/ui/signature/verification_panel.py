"""Panel que muestra el estado de las firmas digitales del documento."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from lectorpdf.core.domain.firma_digital import EstadoFirma, ResultadoVerificacion

_COLORES: dict[EstadoFirma, QColor] = {
    EstadoFirma.VALIDA: QColor(21, 128, 61),  # verde
    EstadoFirma.INVALIDA: QColor(185, 28, 28),  # rojo
    EstadoFirma.DESCONOCIDA: QColor(180, 83, 9),  # ámbar
}
_ETIQUETAS: dict[EstadoFirma, str] = {
    EstadoFirma.VALIDA: "VÁLIDA",
    EstadoFirma.INVALIDA: "INVÁLIDA",
    EstadoFirma.DESCONOCIDA: "DESCONOCIDA",
}


class VerificationPanel(QListWidget):
    def mostrar(self, resultados: tuple[ResultadoVerificacion, ...]) -> None:
        self.clear()
        if not resultados:
            self.addItem(QListWidgetItem("El documento no tiene firmas digitales."))
            return
        for r in resultados:
            texto = (
                f"[{_ETIQUETAS[r.estado]}] {r.firmante}\n{r.motivo}"
                + ("\nCon sello de tiempo" if r.sellada_en_tiempo else "")
            )
            item = QListWidgetItem(texto)
            item.setForeground(_COLORES[r.estado])
            self.addItem(item)

    def filas(self) -> int:
        return self.count()
