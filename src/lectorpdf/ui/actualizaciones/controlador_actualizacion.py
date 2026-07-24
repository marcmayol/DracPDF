"""Controlador de la comprobación de actualizaciones (Fase 10, tarea 3).

Gobierna las tres frecuencias: al arrancar (retrasada, en worker, para no competir
con la restauración de sesión), periódica cada ``check_horas`` con jitter, y manual
(la única que informa del resultado negativo). El ajuste "buscar automáticamente"
vive en QSettings y está activado por defecto. La comprobación corre en un hilo del
pool (no modal); el resultado se emite como señal para que la ventana decida qué
mostrar.
"""

from __future__ import annotations

import secrets
from typing import cast

from PySide6.QtCore import QObject, QSettings, QThreadPool, QTimer, Signal

from lectorpdf.core.domain.actualizacion import ResultadoComprobacion, TipoResultado
from lectorpdf.core.use_cases.comprobar_actualizacion import ComprobarActualizacion
from lectorpdf.ui.tareas import Trabajo

_CLAVE_AUTO = "actualizaciones/automatico"
_CLAVE_ETAG = "actualizaciones/etag"
_CLAVE_HORAS = "actualizaciones/check_horas"

_RETRASO_ARRANQUE_MS = 8000  # unos segundos tras arrancar
_JITTER_MAX_MS = 30 * 60 * 1000  # hasta 30 min de jitter en la periódica
_HORAS_POR_DEFECTO = 24


class ControladorActualizacion(QObject):
    #: Hay una versión nueva: la ventana muestra la banda no modal.
    actualizacion_disponible = Signal(object)  # Manifiesto
    #: Toda comprobación manual termina aquí (para informar al día / error).
    comprobacion_terminada = Signal(object)  # ResultadoComprobacion

    def __init__(
        self,
        caso: ComprobarActualizacion,
        version_actual: str,
        prefs: QSettings,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._caso = caso
        self._version = version_actual
        self._prefs = prefs
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(lambda: self.comprobar(manual=False))
        self._en_curso = False

    # -- Ajuste -------------------------------------------------------------

    def automatico_activado(self) -> bool:
        return bool(self._prefs.value(_CLAVE_AUTO, True, type=bool))

    def set_automatico(self, activado: bool) -> None:
        self._prefs.setValue(_CLAVE_AUTO, activado)
        if not activado:
            self._timer.stop()

    # -- Arranque -----------------------------------------------------------

    def iniciar(self) -> None:
        """Programa la comprobación de arranque (retrasada) si está activada."""
        if self.automatico_activado():
            QTimer.singleShot(_RETRASO_ARRANQUE_MS, lambda: self.comprobar(manual=False))

    # -- Comprobación -------------------------------------------------------

    def comprobar(self, manual: bool) -> None:
        """Lanza la comprobación en un hilo del pool (no modal)."""
        if self._en_curso:
            return
        self._en_curso = True
        etag = self._etag_guardado()
        trabajo = Trabajo(lambda _p: self._caso.ejecutar(self._version, etag))
        trabajo.senales.terminado.connect(lambda res: self._al_terminar(res, manual))
        trabajo.senales.error.connect(lambda exc: self._al_error(exc, manual))
        QThreadPool.globalInstance().start(trabajo)

    def _al_terminar(self, resultado: object, manual: bool) -> None:
        self._en_curso = False
        if isinstance(resultado, ResultadoComprobacion):
            self._procesar(resultado, manual)

    def _al_error(self, exc: object, manual: bool) -> None:
        # El caso de uso no debería propagar, pero por si acaso: se trata como
        # ERROR (silencioso en automático, informado en manual).
        self._en_curso = False
        self._procesar(
            ResultadoComprobacion(TipoResultado.ERROR, error=str(exc)), manual
        )

    def _procesar(self, res: ResultadoComprobacion, manual: bool) -> None:
        if res.etag:
            self._prefs.setValue(_CLAVE_ETAG, res.etag)
        if res.manifiesto is not None:
            self._prefs.setValue(_CLAVE_HORAS, res.manifiesto.check_horas)
        self._reprogramar_periodica()

        if res.tipo is TipoResultado.HAY_ACTUALIZACION and res.manifiesto is not None:
            self.actualizacion_disponible.emit(res.manifiesto)
            if manual:
                self.comprobacion_terminada.emit(res)
        elif manual:
            # Solo la comprobación manual informa de "al día" o del error.
            self.comprobacion_terminada.emit(res)

    # -- Interno ------------------------------------------------------------

    def _etag_guardado(self) -> str | None:
        valor = self._prefs.value(_CLAVE_ETAG, None)
        return str(valor) if valor else None

    def _reprogramar_periodica(self) -> None:
        if not self.automatico_activado():
            return
        horas = cast(int, self._prefs.value(_CLAVE_HORAS, _HORAS_POR_DEFECTO, type=int))
        jitter = secrets.randbelow(_JITTER_MAX_MS)
        self._timer.start(max(1, horas) * 3600 * 1000 + jitter)
