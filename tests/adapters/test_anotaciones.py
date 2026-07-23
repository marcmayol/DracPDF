"""Tests del adaptador de anotaciones/texto PyMuPDF (Fase 9)."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from lectorpdf.adapters.pymupdf.anotaciones import PyMuPDFAnotaciones
from lectorpdf.adapters.pymupdf.document_repository import PyMuPDFDocumentRepository
from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.anotaciones import FuenteTexto, TextoNuevo
from lectorpdf.core.domain.errores import DocumentoFirmado
from lectorpdf.core.domain.formularios import RectanguloPt


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
