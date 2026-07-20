"""Tests de la instancia única (QLocalServer/QLocalSocket)."""

from __future__ import annotations

import uuid

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from lectorpdf.ui.instancia_unica import InstanciaUnica, nombre_servidor


def _nombre() -> str:
    return f"dracpdf-test-{uuid.uuid4().hex[:12]}"


def test_nombre_servidor_por_usuario() -> None:
    assert nombre_servidor().startswith("dracpdf-")


def test_sin_servidor_no_hay_instancia(qapp: object) -> None:
    inst = InstanciaUnica(_nombre())
    assert inst.ya_hay_instancia("x") is False


def test_iniciar_servidor_en_nombre_libre(qapp: object) -> None:
    inst = InstanciaUnica(_nombre())
    assert inst.iniciar_servidor() is True


def test_cliente_envia_ruta_al_servidor(qapp: object) -> None:
    nombre = _nombre()
    servidor = InstanciaUnica(nombre)
    assert servidor.iniciar_servidor() is True

    recibidos: list[str] = []
    bucle = QEventLoop()
    servidor.mensaje_recibido.connect(recibidos.append)
    servidor.mensaje_recibido.connect(lambda _: bucle.quit())

    # Cliente vivo mientras se procesan eventos (un solo hilo en el test; en
    # producción el cliente es otro proceso y basta ya_hay_instancia()).
    cliente = QLocalSocket()
    cliente.connectToServer(nombre)
    assert cliente.waitForConnected(300)
    cliente.write(b"C:/docs/ejemplo.pdf")
    cliente.flush()
    cliente.waitForBytesWritten(300)

    QTimer.singleShot(1000, bucle.quit)  # salvaguarda
    bucle.exec()
    cliente.abort()

    assert recibidos == ["C:/docs/ejemplo.pdf"]


def test_ya_hay_instancia_true_con_servidor(qapp: object) -> None:
    nombre = _nombre()
    servidor = InstanciaUnica(nombre)
    assert servidor.iniciar_servidor() is True

    cliente = InstanciaUnica(nombre)
    assert cliente.ya_hay_instancia("x") is True


def test_recupera_de_nombre_ocupado_por_huerfano(
    qapp: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    inst = InstanciaUnica(_nombre())
    llamadas = {"listen": 0, "remove": 0}
    real_listen = QLocalServer.listen

    def fake_listen(self: QLocalServer, nombre: str) -> bool:
        llamadas["listen"] += 1
        if llamadas["listen"] == 1:
            return False  # simula el nombre ocupado por un socket huérfano
        return bool(real_listen(self, nombre))

    def fake_remove(nombre: str) -> bool:
        llamadas["remove"] += 1
        return True

    monkeypatch.setattr(QLocalServer, "listen", fake_listen)
    monkeypatch.setattr(QLocalServer, "removeServer", staticmethod(fake_remove))

    assert inst.iniciar_servidor() is True
    assert llamadas["remove"] == 1  # se limpió el huérfano antes de reintentar
    assert llamadas["listen"] == 2  # un fallo + un reintento con éxito
