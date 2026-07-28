"""Tests del diálogo de PDF → imágenes (formato, resolución y calidad)."""

from __future__ import annotations

from lectorpdf.core.domain.conversion import FormatoImagen
from lectorpdf.ui.conversion.imagenes_salida_dialog import (
    ConversionImagenesSalidaDialog,
)


def _elegir(dialogo: ConversionImagenesSalidaDialog, formato: FormatoImagen) -> None:
    for fila in range(dialogo._formato.count()):
        dialogo._formato.setCurrentIndex(fila)
        if dialogo.formato() is formato:
            return
    raise AssertionError(f"El diálogo no ofrece {formato}")


def test_png_por_defecto_sin_calidad(qapp: object) -> None:
    dialogo = ConversionImagenesSalidaDialog()

    assert dialogo.formato() is FormatoImagen.PNG
    assert not dialogo._calidad.isEnabled()  # PNG no tiene pérdida
    assert dialogo._dpi.isEnabled()


def test_la_calidad_solo_se_activa_en_formatos_con_perdida(qapp: object) -> None:
    dialogo = ConversionImagenesSalidaDialog()

    for formato in (FormatoImagen.JPEG, FormatoImagen.WEBP):
        _elegir(dialogo, formato)
        assert dialogo._calidad.isEnabled(), formato

    for formato in (FormatoImagen.PNG, FormatoImagen.TIFF, FormatoImagen.SVG):
        _elegir(dialogo, formato)
        assert not dialogo._calidad.isEnabled(), formato


def test_el_svg_no_pide_resolucion_y_lo_explica(qapp: object) -> None:
    dialogo = ConversionImagenesSalidaDialog()

    _elegir(dialogo, FormatoImagen.SVG)

    assert not dialogo._dpi.isEnabled()  # vectorial: el DPI no pinta nada
    assert "resolución" in dialogo._nota.text()


def test_el_tiff_avisa_de_que_es_un_solo_fichero(qapp: object) -> None:
    dialogo = ConversionImagenesSalidaDialog()

    _elegir(dialogo, FormatoImagen.TIFF)

    assert "mismo fichero" in dialogo._nota.text()
