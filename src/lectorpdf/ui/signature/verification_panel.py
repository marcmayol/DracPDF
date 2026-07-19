"""Panel que muestra el estado de las firmas digitales del documento.

Cada firma es una tarjeta (QFrame[sigCard]) con la propiedad dinámica sigState;
el color del borde y del estado los pone el QSS desde los tokens semánticos del
diseño (sig-valid/invalid/unknown). Aquí no hay ningún color literal.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from lectorpdf.core.domain.firma_digital import EstadoFirma, ResultadoVerificacion

_PROP_ESTADO: dict[EstadoFirma, str] = {
    EstadoFirma.VALIDA: "valid",
    EstadoFirma.INVALIDA: "invalid",
    EstadoFirma.DESCONOCIDA: "unknown",
}
_ETIQUETAS: dict[EstadoFirma, str] = {
    EstadoFirma.VALIDA: "VÁLIDA",
    EstadoFirma.INVALIDA: "INVÁLIDA",
    EstadoFirma.DESCONOCIDA: "DESCONOCIDA",
}


class VerificationPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(8)
        self._layout.addStretch(1)

    def mostrar(self, resultados: tuple[ResultadoVerificacion, ...]) -> None:
        self._vaciar()
        if not resultados:
            self._layout.insertWidget(0, QLabel("El documento no tiene firmas digitales."))
            return
        for indice, resultado in enumerate(resultados):
            self._layout.insertWidget(indice, _tarjeta(resultado))

    def tarjetas(self) -> int:
        total = 0
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is not None and widget.property("sigCard") is True:
                total += 1
        return total

    def _vaciar(self) -> None:
        while self._layout.count() > 1:  # deja el stretch final
            item = self._layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()


def _tarjeta(resultado: ResultadoVerificacion) -> QFrame:
    prop = _PROP_ESTADO[resultado.estado]
    tarjeta = QFrame()
    tarjeta.setProperty("sigCard", True)
    tarjeta.setProperty("sigState", prop)

    layout = QVBoxLayout(tarjeta)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(4)

    estado = QLabel(f"{_ETIQUETAS[resultado.estado]} · {resultado.firmante}")
    estado.setProperty("sigState", prop)
    motivo = QLabel(resultado.motivo)
    motivo.setWordWrap(True)
    layout.addWidget(estado)
    layout.addWidget(motivo)
    if resultado.sellada_en_tiempo:
        layout.addWidget(QLabel("Con sello de tiempo"))
    return tarjeta
