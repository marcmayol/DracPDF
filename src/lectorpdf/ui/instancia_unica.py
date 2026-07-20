"""Instancia única de la aplicación mediante QLocalServer/QLocalSocket.

Al arrancar se intenta conectar como cliente al servidor local con nombre por
usuario. Si alguien responde, ya hay una instancia: se le envía el documento a
abrir y esta invocación termina. Si nadie responde, se arranca como servidor; si
el nombre quedó registrado por una instancia que no cerró limpio (socket
huérfano), se elimina y se reintenta.

Está deshabilitado en los tests: solo lo activa el punto de entrada de la app.
"""

from __future__ import annotations

import getpass
import re

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

_TIMEOUT_MS = 300


def nombre_servidor() -> str:
    """Nombre del servidor local, por usuario: `dracpdf-<usuario>`."""
    try:
        usuario = getpass.getuser()
    except Exception:  # pragma: no cover - entornos sin usuario
        usuario = "anon"
    usuario = re.sub(r"[^A-Za-z0-9_-]", "_", usuario) or "anon"
    return f"dracpdf-{usuario}"


class InstanciaUnica(QObject):
    #: Otra invocación pide abrir un documento (ruta, o "" si no pasó ninguno).
    mensaje_recibido = Signal(str)

    def __init__(self, nombre: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._nombre = nombre
        self._servidor: QLocalServer | None = None
        self._pendientes: list[QLocalSocket] = []

    def ya_hay_instancia(self, mensaje: str = "") -> bool:
        """Intenta conectar como cliente. Si responde, le envía `mensaje` (la ruta
        a abrir) y devuelve True: esta invocación debe terminar."""
        socket = QLocalSocket()
        socket.connectToServer(self._nombre)
        if not socket.waitForConnected(_TIMEOUT_MS):
            return False
        socket.write(mensaje.encode("utf-8"))
        socket.flush()
        socket.waitForBytesWritten(_TIMEOUT_MS)
        socket.disconnectFromServer()
        return True

    def iniciar_servidor(self) -> bool:
        """Arranca el servidor local. Si el nombre estaba registrado por un socket
        huérfano (nadie escuchando), lo elimina y reintenta una vez."""
        self._servidor = QLocalServer()
        if not self._servidor.listen(self._nombre):
            QLocalServer.removeServer(self._nombre)
            if not self._servidor.listen(self._nombre):
                return False
        self._servidor.newConnection.connect(self._al_conectar)
        return True

    def _al_conectar(self) -> None:
        if self._servidor is None:
            return
        socket = self._servidor.nextPendingConnection()
        if socket is None:
            return
        # Lectura asíncrona: la ruta puede no haber llegado aún al aceptar.
        self._pendientes.append(socket)
        socket.readyRead.connect(lambda: self._al_leer(socket))
        if socket.bytesAvailable() > 0:
            self._al_leer(socket)

    def _al_leer(self, socket: QLocalSocket) -> None:
        if socket.bytesAvailable() <= 0:
            return
        mensaje = bytes(socket.readAll().data()).decode("utf-8", "replace")
        self.mensaje_recibido.emit(mensaje)
        socket.disconnectFromServer()
        if socket in self._pendientes:
            self._pendientes.remove(socket)
