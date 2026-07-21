"""Tests del widget de estado vacío (sin documento)."""

from __future__ import annotations

from lectorpdf.ui.estado_vacio import EstadoVacio
from lectorpdf.ui.theme import tokens


def test_silueta_se_tinta_al_recolorear(qapp: object) -> None:
    estado = EstadoVacio()
    estado.recolorear(tokens.TEMA_OSCURO.text_muted)

    # Hay una marca de agua (silueta tintada) tras recolorear.
    pixmap = estado._silueta.pixmap()
    assert not pixmap.isNull()


def test_boton_abrir_emite_senal(qapp: object) -> None:
    estado = EstadoVacio()
    disparos: list[bool] = []
    estado.abrir_solicitado.connect(lambda: disparos.append(True))

    estado._boton.click()

    assert disparos == [True]


def test_recientes_clicables_emiten_su_ruta(qapp: object) -> None:
    estado = EstadoVacio()
    estado.set_recientes(["/docs/a.pdf", "/docs/b.pdf"])
    elegidas: list[str] = []
    estado.reciente_elegido.connect(elegidas.append)

    estado._recientes[1].click()

    assert elegidas == ["/docs/b.pdf"]


def test_recientes_se_limitan_a_cuatro(qapp: object) -> None:
    estado = EstadoVacio()
    estado.set_recientes([f"/docs/{i}.pdf" for i in range(10)])

    assert len(estado._recientes) == 4
