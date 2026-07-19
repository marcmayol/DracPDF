"""Ejecución de operaciones largas en un hilo, con progreso y cancelación.

Toda la concurrencia vive aquí (UI). El caso de uso del core es una función
síncrona que recibe un callback de progreso del dominio; este módulo lo envuelve
en un QRunnable que lo ejecuta en el pool de hilos y traduce el progreso, el
resultado, el error y la cancelación a señales Qt y a un QProgressDialog modal.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import (
    QEventLoop,
    QObject,
    QRunnable,
    Qt,
    QThreadPool,
    Signal,
)
from PySide6.QtWidgets import QProgressDialog, QWidget

from lectorpdf.core.domain.errores import OperacionCancelada
from lectorpdf.core.domain.herramientas import Progreso

#: La función de trabajo recibe el callback de progreso y devuelve un resultado.
FuncionTarea = Callable[[Progreso], object]


class _SenalesTrabajo(QObject):
    progreso = Signal(int, int)
    terminado = Signal(object)
    error = Signal(object)
    cancelado = Signal()


class Trabajo(QRunnable):
    def __init__(self, funcion: FuncionTarea) -> None:
        super().__init__()
        self._funcion = funcion
        self._cancelar = False
        self.senales = _SenalesTrabajo()

    def cancelar(self) -> None:
        self._cancelar = True

    def _progreso(self, hecho: int, total: int) -> None:
        if self._cancelar:
            raise OperacionCancelada()
        self.senales.progreso.emit(hecho, total)

    def run(self) -> None:
        try:
            resultado = self._funcion(self._progreso)
        except OperacionCancelada:
            self.senales.cancelado.emit()
        except Exception as exc:  # se traslada a la UI como error
            self.senales.error.emit(exc)
        else:
            self.senales.terminado.emit(resultado)


@dataclass
class ResultadoTarea:
    resultado: object = None
    error: Exception | None = None
    cancelado: bool = False


def ejecutar_con_progreso(
    parent: QWidget | None, titulo: str, funcion: FuncionTarea
) -> ResultadoTarea:
    """Ejecuta `funcion` en un hilo mostrando un diálogo modal de progreso.

    Devuelve el resultado, o marca error/cancelado. La UI no se congela: se usa
    un bucle de eventos local mientras corre el trabajo.
    """
    dialogo = QProgressDialog(titulo, "Cancelar", 0, 0, parent)
    dialogo.setWindowModality(Qt.WindowModality.WindowModal)
    dialogo.setMinimumDuration(0)

    trabajo = Trabajo(funcion)
    estado = ResultadoTarea()
    bucle = QEventLoop()

    def _progreso(hecho: int, total: int) -> None:
        if total > 0:
            dialogo.setMaximum(total)
        dialogo.setValue(hecho)

    def _terminado(resultado: object) -> None:
        estado.resultado = resultado
        bucle.quit()

    def _error(exc: object) -> None:
        estado.error = exc if isinstance(exc, Exception) else RuntimeError(str(exc))
        bucle.quit()

    def _cancelado() -> None:
        estado.cancelado = True
        bucle.quit()

    trabajo.senales.progreso.connect(_progreso)
    trabajo.senales.terminado.connect(_terminado)
    trabajo.senales.error.connect(_error)
    trabajo.senales.cancelado.connect(_cancelado)
    dialogo.canceled.connect(trabajo.cancelar)

    QThreadPool.globalInstance().start(trabajo)
    dialogo.show()
    bucle.exec()
    dialogo.close()
    return estado
