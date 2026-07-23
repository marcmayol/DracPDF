"""Tests del adaptador de anotaciones/texto PyMuPDF (Fase 9)."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from lectorpdf.adapters.pymupdf.anotaciones import PyMuPDFAnotaciones
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.anotaciones import (
    Correccion,
    FuenteTexto,
    ImagenNueva,
    Nota,
    TextoNuevo,
    TipoMarcado,
)
from lectorpdf.core.domain.errores import DocumentoFirmado, TextoNoCabe
from lectorpdf.core.domain.formularios import RectanguloPt


def _n_annots(page: fitz.Page) -> int:
    return len(list(page.annots()))


def _pdf(tmp_path: Path) -> Path:
    ruta = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page(width=400, height=500)
    doc.save(ruta)
    doc.close()
    return ruta


def _abrir(ruta: Path) -> tuple[PyMuPDFAnotaciones, str, RegistroDocumentos]:
    registro = RegistroDocumentos()
    repo = PyMuPDFDocumentRepository(registro)
    servicio = PyMuPDFAnotaciones(registro)
    documento = repo.abrir(ruta)
    return servicio, documento.id, registro


def _texto(txt: str = "Texto añadido áéí") -> TextoNuevo:
    return TextoNuevo(
        rect_pt=RectanguloPt(40, 40, 360, 90),
        texto=txt,
        fuente=FuenteTexto.SANS,
        tamano=14.0,
        color=(0.1, 0.1, 0.1),
    )


def _fuente_embebida(page: fitz.Page) -> bool:
    return any(f[2] == "Type0" and f[1] == "ttf" for f in page.get_fonts(full=True))


def _texto_de(page: fitz.Page) -> str:
    # insert_textbox separa palabras con espacio duro (U+00A0); se normaliza.
    return page.get_text().replace("\xa0", " ")


def test_anadir_texto_hornea_con_fuente_embebida_y_marca(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))

    servicio.anadir_texto(doc_id, 0, _texto())

    page = registro.obtener(doc_id)[0]
    assert "Texto añadido" in _texto_de(page)
    assert _fuente_embebida(page) is True
    assert registro.tiene(doc_id, Marca.CAMBIOS_SIN_GUARDAR) is True
    registro.cerrar(doc_id)


def test_texto_sobrevive_a_guardar_y_reabrir(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    servicio.anadir_texto(doc_id, 0, _texto())
    salida = tmp_path / "con_texto.pdf"
    registro.obtener(doc_id).save(str(salida))
    registro.cerrar(doc_id)

    reabierto = fitz.open(salida)
    assert "Texto añadido" in _texto_de(reabierto[0])
    assert _fuente_embebida(reabierto[0]) is True
    reabierto.close()


def test_deshacer_quita_el_texto_y_rehacer_lo_devuelve(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    servicio.anadir_texto(doc_id, 0, _texto())
    assert servicio.puede_deshacer(doc_id) is True

    paginas = servicio.deshacer(doc_id)
    assert paginas == (0,)
    assert "Texto añadido" not in _texto_de(registro.obtener(doc_id)[0])

    paginas = servicio.rehacer(doc_id)
    assert paginas == (0,)
    assert "Texto añadido" in _texto_de(registro.obtener(doc_id)[0])
    registro.cerrar(doc_id)


def test_deshacer_sobrevive_a_reabrir(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    servicio.anadir_texto(doc_id, 0, _texto())
    servicio.deshacer(doc_id)
    salida = tmp_path / "deshecho.pdf"
    registro.obtener(doc_id).save(str(salida))
    registro.cerrar(doc_id)

    reabierto = fitz.open(salida)
    assert "Texto añadido" not in _texto_de(reabierto[0])
    reabierto.close()


def test_rechaza_en_documento_firmado(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    registro.marcar(doc_id, Marca.FIRMADO)

    with pytest.raises(DocumentoFirmado):
        servicio.anadir_texto(doc_id, 0, _texto())
    registro.cerrar(doc_id)


# -- Tarea 2: marcado y borrado de anotaciones ------------------------------

_RECT = RectanguloPt(50, 60, 200, 75)


def test_marcar_crea_anotacion_estandar_y_sobrevive_reabrir(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    servicio.marcar(doc_id, 0, (_RECT,), TipoMarcado.RESALTADO, (1.0, 0.9, 0.2))

    page = registro.obtener(doc_id)[0]
    assert "Highlight" in [a.type[1] for a in page.annots()]
    assert registro.tiene(doc_id, Marca.CAMBIOS_SIN_GUARDAR) is True

    salida = tmp_path / "marcado.pdf"
    page.parent.save(str(salida))
    registro.cerrar(doc_id)
    reabierto = fitz.open(salida)
    assert _n_annots(reabierto[0]) == 1
    reabierto.close()


def test_deshacer_marcado_lo_quita_y_rehacer_lo_devuelve(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    servicio.marcar(doc_id, 0, (_RECT,), TipoMarcado.SUBRAYADO, (0.9, 0.3, 0.3))
    assert _n_annots(registro.obtener(doc_id)[0]) == 1

    servicio.deshacer(doc_id)
    assert _n_annots(registro.obtener(doc_id)[0]) == 0

    servicio.rehacer(doc_id)
    assert _n_annots(registro.obtener(doc_id)[0]) == 1
    registro.cerrar(doc_id)


def test_anotacion_en_localiza_y_eliminar_la_quita(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    servicio.marcar(doc_id, 0, (_RECT,), TipoMarcado.TACHADO, (0.2, 0.2, 0.2))

    xref = servicio.anotacion_en(doc_id, 0, 100.0, 67.0)
    assert xref is not None
    assert servicio.anotacion_en(doc_id, 0, 5.0, 5.0) is None  # fuera del rect

    servicio.eliminar_anotacion(doc_id, 0, xref)
    assert _n_annots(registro.obtener(doc_id)[0]) == 0
    registro.cerrar(doc_id)


def test_marcar_rechaza_en_firmado(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    registro.marcar(doc_id, Marca.FIRMADO)

    with pytest.raises(DocumentoFirmado):
        servicio.marcar(doc_id, 0, (_RECT,), TipoMarcado.RESALTADO, (1.0, 0.9, 0.2))
    registro.cerrar(doc_id)


# -- Tarea 3: nota adhesiva -------------------------------------------------


def test_nota_crea_anotacion_texto_y_sobrevive_reabrir(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    servicio.anadir_nota(doc_id, 0, Nota(80.0, 100.0, "Revisar esto"))

    page = registro.obtener(doc_id)[0]
    assert "Text" in [a.type[1] for a in page.annots()]

    salida = tmp_path / "nota.pdf"
    page.parent.save(str(salida))
    registro.cerrar(doc_id)
    reabierto = fitz.open(salida)
    contenidos = [a.info["content"] for a in reabierto[0].annots()]
    assert "Revisar esto" in contenidos
    reabierto.close()


def test_deshacer_nota_la_quita(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf(tmp_path))
    servicio.anadir_nota(doc_id, 0, Nota(80.0, 100.0, "Nota"))
    assert _n_annots(registro.obtener(doc_id)[0]) == 1

    servicio.deshacer(doc_id)
    assert _n_annots(registro.obtener(doc_id)[0]) == 0
    registro.cerrar(doc_id)


# -- Tareas 6-7: corrección de texto ----------------------------------------


def _pdf_texto(tmp_path: Path) -> Path:
    ruta = tmp_path / "t.pdf"
    doc = fitz.open()
    p = doc.new_page(width=420, height=200)
    p.insert_text((40, 90), "El pago es CINCUENTA euros exactos.", fontsize=13)
    doc.save(ruta)
    doc.close()
    return ruta


def _rect_pt_de(registro: RegistroDocumentos, doc_id: str, tramo: str) -> RectanguloPt:
    r = registro.obtener(doc_id)[0].search_for(tramo)[0]
    return RectanguloPt(r.x0, r.y0, r.x1, r.y1)


def test_corregir_elimina_original_y_escribe_nuevo(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf_texto(tmp_path))
    rect = _rect_pt_de(registro, doc_id, "CINCUENTA")
    servicio.corregir_texto(
        doc_id, 0, Correccion(rect, "OCHENTA", FuenteTexto.SERIF, (0.0, 0.0, 0.0))
    )
    salida = tmp_path / "corr.pdf"
    registro.obtener(doc_id).save(str(salida))
    registro.cerrar(doc_id)

    reabierto = fitz.open(salida)
    texto = _texto_de(reabierto[0])
    assert "CINCUENTA" not in texto  # original realmente eliminado
    assert "OCHENTA" in texto
    assert _fuente_embebida(reabierto[0]) is True
    reabierto.close()


def test_cabe_texto_detecta_ancho(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf_texto(tmp_path))
    rect = _rect_pt_de(registro, doc_id, "CINCUENTA")
    assert servicio.cabe_texto(doc_id, 0, rect, "OCHENTA", FuenteTexto.SERIF) is True
    assert (
        servicio.cabe_texto(doc_id, 0, rect, "PALABRALARGUISIMAQUENOCABE", FuenteTexto.SERIF)
        is False
    )
    registro.cerrar(doc_id)


def test_no_cabe_lanza_y_reducir_encaja(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf_texto(tmp_path))
    rect = _rect_pt_de(registro, doc_id, "CINCUENTA")
    largo = "PALABRALARGUISIMAQUENOCABE"

    with pytest.raises(TextoNoCabe):
        servicio.corregir_texto(
            doc_id, 0, Correccion(rect, largo, FuenteTexto.SANS, (0.0, 0.0, 0.0))
        )
    servicio.corregir_texto(
        doc_id, 0, Correccion(rect, largo, FuenteTexto.SANS, (0.0, 0.0, 0.0), reducir=True)
    )
    assert largo in _texto_de(registro.obtener(doc_id)[0])
    registro.cerrar(doc_id)


def test_deshacer_correccion_restaura_el_original(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf_texto(tmp_path))
    rect = _rect_pt_de(registro, doc_id, "CINCUENTA")
    servicio.corregir_texto(
        doc_id, 0, Correccion(rect, "OCHENTA", FuenteTexto.SERIF, (0.0, 0.0, 0.0))
    )
    assert "CINCUENTA" not in _texto_de(registro.obtener(doc_id)[0])

    servicio.deshacer(doc_id)
    assert "CINCUENTA" in _texto_de(registro.obtener(doc_id)[0])
    registro.cerrar(doc_id)


def test_corregir_rechaza_en_firmado(tmp_path: Path) -> None:
    servicio, doc_id, registro = _abrir(_pdf_texto(tmp_path))
    rect = _rect_pt_de(registro, doc_id, "CINCUENTA")
    registro.marcar(doc_id, Marca.FIRMADO)
    with pytest.raises(DocumentoFirmado):
        servicio.corregir_texto(
            doc_id, 0, Correccion(rect, "OCHENTA", FuenteTexto.SERIF, (0.0, 0.0, 0.0))
        )
    registro.cerrar(doc_id)


# -- Imágenes (Parte C) -----------------------------------------------------


def _png(tmp_path: Path, color: tuple[int, int, int] = (220, 40, 40)) -> Path:
    ruta = tmp_path / "img.png"
    pm = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 24, 24), 0)
    pm.set_rect(pm.irect, color)
    pm.save(str(ruta))
    return ruta


def _pdf_con_imagen(tmp_path: Path, veces_paginas: int = 1) -> tuple[Path, Path]:
    """PDF con una imagen roja en (60,80,180,200) de la primera página. Si
    `veces_paginas` > 1, la misma imagen se coloca también en páginas extra."""
    png = _png(tmp_path)
    ruta = tmp_path / "con_img.pdf"
    doc = fitz.open()
    for _ in range(veces_paginas):
        p = doc.new_page(width=300, height=300)
        p.insert_text((30, 40), "Texto junto a la imagen", fontsize=11)
        p.insert_image(fitz.Rect(60, 80, 180, 200), filename=str(png))
    doc.save(ruta)
    doc.close()
    return ruta, png


def _color_centro(page: fitz.Page, rect_pt: RectanguloPt) -> tuple[int, int, int]:
    r = fitz.Rect(rect_pt.x0, rect_pt.y0, rect_pt.x1, rect_pt.y1) + (2, 2, -2, -2)
    pix = page.get_pixmap(clip=r, dpi=72)
    return pix.pixel(pix.width // 2, pix.height // 2)


def test_anadir_imagen_inserta_y_sobrevive_a_reabrir(tmp_path: Path) -> None:
    ruta = tmp_path / "vacio.pdf"
    doc = fitz.open()
    doc.new_page(width=300, height=300)
    doc.save(ruta)
    doc.close()
    png = _png(tmp_path)
    servicio, doc_id, registro = _abrir(ruta)

    rect = RectanguloPt(50, 50, 170, 170)
    servicio.anadir_imagen(doc_id, 0, ImagenNueva(rect, png))
    page = registro.obtener(doc_id)[0]
    assert len(page.get_images()) == 1
    assert _color_centro(page, rect) == (220, 40, 40)
    assert registro.tiene(doc_id, Marca.CAMBIOS_SIN_GUARDAR) is True

    salida = tmp_path / "con.pdf"
    registro.obtener(doc_id).save(str(salida))
    registro.cerrar(doc_id)
    reabierto = fitz.open(salida)
    assert len(reabierto[0].get_images()) == 1
    reabierto.close()


def test_anadir_imagen_inexistente_falla(tmp_path: Path) -> None:
    ruta = tmp_path / "vacio.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(ruta)
    doc.close()
    servicio, doc_id, registro = _abrir(ruta)
    with pytest.raises(fitz.FileNotFoundError):
        servicio.anadir_imagen(
            doc_id, 0, ImagenNueva(RectanguloPt(10, 10, 50, 50), tmp_path / "no.png")
        )
    registro.cerrar(doc_id)


def test_deshacer_anadir_imagen(tmp_path: Path) -> None:
    ruta = tmp_path / "vacio.pdf"
    doc = fitz.open()
    doc.new_page(width=300, height=300)
    doc.save(ruta)
    doc.close()
    png = _png(tmp_path)
    servicio, doc_id, registro = _abrir(ruta)
    rect = RectanguloPt(50, 50, 170, 170)
    servicio.anadir_imagen(doc_id, 0, ImagenNueva(rect, png))
    assert _color_centro(registro.obtener(doc_id)[0], rect) == (220, 40, 40)

    servicio.deshacer(doc_id)
    assert _color_centro(registro.obtener(doc_id)[0], rect) == (255, 255, 255)
    servicio.rehacer(doc_id)
    assert _color_centro(registro.obtener(doc_id)[0], rect) == (220, 40, 40)
    registro.cerrar(doc_id)


def test_imagenes_en_detecta_rect_y_metadatos(tmp_path: Path) -> None:
    ruta, _ = _pdf_con_imagen(tmp_path)
    servicio, doc_id, registro = _abrir(ruta)
    imagenes = servicio.imagenes_en(doc_id, 0)
    assert len(imagenes) == 1
    img = imagenes[0]
    assert img.rect_pt.x0 == pytest.approx(60, abs=1)
    assert img.en_varias_paginas is False
    assert img.cubre_pagina is False
    registro.cerrar(doc_id)


def test_imagen_que_cubre_pagina_se_avisa(tmp_path: Path) -> None:
    png = _png(tmp_path)
    ruta = tmp_path / "escan.pdf"
    doc = fitz.open()
    p = doc.new_page(width=300, height=300)
    p.insert_image(fitz.Rect(0, 0, 300, 300), filename=str(png))
    doc.save(ruta)
    doc.close()
    servicio, doc_id, registro = _abrir(ruta)
    img = servicio.imagenes_en(doc_id, 0)[0]
    assert img.cubre_pagina is True
    registro.cerrar(doc_id)


def test_imagen_en_varias_paginas_se_avisa(tmp_path: Path) -> None:
    ruta, _ = _pdf_con_imagen(tmp_path, veces_paginas=2)
    servicio, doc_id, registro = _abrir(ruta)
    img = servicio.imagenes_en(doc_id, 0)[0]
    assert img.en_varias_paginas is True
    registro.cerrar(doc_id)


def test_imagen_en_punto_localiza(tmp_path: Path) -> None:
    ruta, _ = _pdf_con_imagen(tmp_path)
    servicio, doc_id, registro = _abrir(ruta)
    assert servicio.imagen_en(doc_id, 0, 120, 140) is not None
    assert servicio.imagen_en(doc_id, 0, 5, 5) is None
    registro.cerrar(doc_id)


def test_eliminar_imagen_y_deshacer(tmp_path: Path) -> None:
    ruta, _ = _pdf_con_imagen(tmp_path)
    servicio, doc_id, registro = _abrir(ruta)
    img = servicio.imagenes_en(doc_id, 0)[0]
    page = registro.obtener(doc_id)[0]
    assert _color_centro(page, img.rect_pt) == (220, 40, 40)

    servicio.eliminar_imagen(doc_id, 0, img)
    assert _color_centro(registro.obtener(doc_id)[0], img.rect_pt) == (255, 255, 255)
    assert registro.tiene(doc_id, Marca.CAMBIOS_SIN_GUARDAR) is True
    # El texto vecino no se toca.
    assert "Texto junto a la imagen" in _texto_de(registro.obtener(doc_id)[0])

    servicio.deshacer(doc_id)
    assert _color_centro(registro.obtener(doc_id)[0], img.rect_pt) == (220, 40, 40)
    registro.cerrar(doc_id)


def test_eliminar_imagen_sobrevive_a_reabrir(tmp_path: Path) -> None:
    ruta, _ = _pdf_con_imagen(tmp_path)
    servicio, doc_id, registro = _abrir(ruta)
    img = servicio.imagenes_en(doc_id, 0)[0]
    servicio.eliminar_imagen(doc_id, 0, img)
    salida = tmp_path / "sin_img.pdf"
    registro.obtener(doc_id).save(str(salida))
    registro.cerrar(doc_id)

    reabierto = fitz.open(salida)
    assert _color_centro(reabierto[0], img.rect_pt) == (255, 255, 255)
    reabierto.close()


def test_eliminar_imagen_rechaza_en_firmado(tmp_path: Path) -> None:
    ruta, _ = _pdf_con_imagen(tmp_path)
    servicio, doc_id, registro = _abrir(ruta)
    img = servicio.imagenes_en(doc_id, 0)[0]
    registro.marcar(doc_id, Marca.FIRMADO)
    with pytest.raises(DocumentoFirmado):
        servicio.eliminar_imagen(doc_id, 0, img)
    registro.cerrar(doc_id)
