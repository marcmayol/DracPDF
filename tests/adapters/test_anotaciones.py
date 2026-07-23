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
