"""Fakes de los puertos para testear casos de uso sin infraestructura."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from lectorpdf.core.domain.contenido import Coincidencia
from lectorpdf.core.domain.errores import CampoNoEncontrado, DocumentoNoAbierto
from lectorpdf.core.domain.firma_digital import (
    ConfigFirma,
    CredencialFirma,
    ResultadoVerificacion,
)
from lectorpdf.core.domain.formularios import (
    CambioValor,
    CampoFormulario,
    RectanguloPt,
)
from lectorpdf.core.domain.herramientas import Progreso, Rango, ResultadoCompresion
from lectorpdf.core.domain.modelos import Documento, ImagenRenderizada, Pagina


class FakeDocumentRepository:
    """Fake en memoria de `DocumentRepository`. Registra las llamadas recibidas."""

    def __init__(
        self,
        documento: Documento | None = None,
        imagen: ImagenRenderizada | None = None,
    ) -> None:
        self._documento = documento
        self._imagen = imagen or ImagenRenderizada(
            ancho_px=1, alto_px=1, datos=b"\x00\x00\x00\x00", escala=1.0
        )
        self.abrir_llamado_con: Path | None = None
        self.render_llamado_con: tuple[str, int, float] | None = None
        self.render_llamadas: list[tuple[str, int, float]] = []
        self.cerrado: list[str] = []

    def abrir(self, ruta: Path) -> Documento:
        self.abrir_llamado_con = ruta
        if self._documento is None:
            raise AssertionError("El fake no tiene un documento configurado")
        return self._documento

    def renderizar_pagina(
        self, documento_id: str, indice: int, escala: float
    ) -> ImagenRenderizada:
        if self._documento is not None and documento_id != self._documento.id:
            raise DocumentoNoAbierto(documento_id)
        self.render_llamado_con = (documento_id, indice, escala)
        self.render_llamadas.append((documento_id, indice, escala))
        return self._imagen

    def cerrar(self, documento_id: str) -> None:
        self.cerrado.append(documento_id)


class FakeFormService:
    """Fake en memoria de `FormService`. Registra escrituras y guardados."""

    def __init__(
        self,
        campos: tuple[CampoFormulario, ...] = (),
        es_xfa: bool = False,
        firmado: bool = False,
    ) -> None:
        self._campos = campos
        self._es_xfa = es_xfa
        self._firmado = firmado
        self.escrituras: list[tuple[str, str, str]] = []
        self.guardados: list[tuple[str, Path | None]] = []
        self.sucio = False
        # Historial de valores (para deshacer/rehacer).
        self._valores: dict[str, str] = {}
        self._ediciones: list[tuple[str, str, str]] = []  # (campo, antes, despues)
        self._pos = 0

    def es_xfa(self, documento_id: str) -> bool:
        return self._es_xfa

    def listar_campos(self, documento_id: str) -> tuple[CampoFormulario, ...]:
        return self._campos

    def escribir_valor(self, documento_id: str, campo_id: str, valor: str) -> None:
        if all(c.id != campo_id for c in self._campos):
            raise CampoNoEncontrado(campo_id)
        antes = self._valores.get(campo_id, "")
        self._valores[campo_id] = valor
        del self._ediciones[self._pos :]
        self._ediciones.append((campo_id, antes, valor))
        self._pos += 1
        self.escrituras.append((documento_id, campo_id, valor))
        self.sucio = True

    def esta_sucio(self, documento_id: str) -> bool:
        return self.sucio

    def esta_firmado(self, documento_id: str) -> bool:
        return self._firmado

    def puede_deshacer(self, documento_id: str) -> bool:
        return self._pos > 0

    def puede_rehacer(self, documento_id: str) -> bool:
        return self._pos < len(self._ediciones)

    def deshacer(self, documento_id: str) -> CambioValor | None:
        if self._pos <= 0:
            return None
        self._pos -= 1
        campo_id, antes, _ = self._ediciones[self._pos]
        self._valores[campo_id] = antes
        return CambioValor(campo_id, antes)

    def rehacer(self, documento_id: str) -> CambioValor | None:
        if self._pos >= len(self._ediciones):
            return None
        campo_id, _, despues = self._ediciones[self._pos]
        self._pos += 1
        self._valores[campo_id] = despues
        return CambioValor(campo_id, despues)

    def guardar_incremental(self, documento_id: str, destino: Path | None) -> None:
        self.guardados.append((documento_id, destino))
        self.sucio = False


class FakeEstampadoService:
    """Fake en memoria de `EstampadoService`. Registra los estampados."""

    def __init__(self) -> None:
        self.estampados: list[tuple[str, int, RectanguloPt, bytes]] = []

    def estampar_imagen(
        self,
        documento_id: str,
        pagina: int,
        rect_pt: RectanguloPt,
        imagen_png: bytes,
    ) -> None:
        self.estampados.append((documento_id, pagina, rect_pt, imagen_png))


class FakeSignatureService:
    """Fake en memoria de `SignatureService`."""

    def __init__(self, resultados: tuple[ResultadoVerificacion, ...] = ()) -> None:
        self._resultados = resultados
        self.firmas: list[tuple[str, ConfigFirma, CredencialFirma]] = []
        self.verificaciones: list[str] = []

    def firmar(
        self,
        documento_id: str,
        config: ConfigFirma,
        credencial: CredencialFirma,
    ) -> None:
        self.firmas.append((documento_id, config, credencial))

    def verificar(
        self,
        documento_id: str,
        anclas_confianza: Sequence[Path],
    ) -> tuple[ResultadoVerificacion, ...]:
        self.verificaciones.append(documento_id)
        return self._resultados


class FakeServicioHerramientas:
    """Fake en memoria de `ServicioHerramientas`. Registra las llamadas."""

    def __init__(self) -> None:
        self.uniones: list[tuple[list[Path], Path]] = []
        self.desprotecciones: list[tuple[Path, str, Path]] = []
        self.rotaciones: list[tuple[str, int, int]] = []
        self.eliminaciones: list[tuple[str, int]] = []
        self.movimientos: list[tuple[str, int, int]] = []
        self.divisiones: list[tuple[str, list[Rango], Path]] = []
        self.protecciones: list[tuple[str, Path, str]] = []
        self.compresiones: list[tuple[str, Path]] = []
        self.exportaciones_png: list[tuple[str, Path, int]] = []
        self.exportaciones_texto: list[tuple[str, Path]] = []
        # Valores devueltos configurables.
        self.paginas_resultado: tuple[Pagina, ...] = ()
        self.rutas_division: list[Path] = []
        self.rutas_png: list[Path] = []
        self.resultado_compresion = ResultadoCompresion(bytes_antes=100, bytes_despues=40)

    def unir(
        self, rutas: Sequence[Path], destino: Path, progreso: Progreso | None = None
    ) -> None:
        if progreso is not None:
            progreso(len(rutas), len(rutas))
        self.uniones.append((list(rutas), destino))

    def desproteger(self, ruta: Path, contrasena: str, destino: Path) -> None:
        self.desprotecciones.append((ruta, contrasena, destino))

    def rotar_pagina(
        self, documento_id: str, indice: int, grados: int
    ) -> tuple[Pagina, ...]:
        self.rotaciones.append((documento_id, indice, grados))
        return self.paginas_resultado

    def eliminar_pagina(
        self, documento_id: str, indice: int
    ) -> tuple[Pagina, ...]:
        self.eliminaciones.append((documento_id, indice))
        return self.paginas_resultado

    def mover_pagina(
        self, documento_id: str, origen: int, destino: int
    ) -> tuple[Pagina, ...]:
        self.movimientos.append((documento_id, origen, destino))
        return self.paginas_resultado

    def dividir(
        self, documento_id: str, rangos: Sequence[Rango], directorio: Path
    ) -> list[Path]:
        self.divisiones.append((documento_id, list(rangos), directorio))
        return self.rutas_division

    def proteger(self, documento_id: str, destino: Path, contrasena: str) -> None:
        self.protecciones.append((documento_id, destino, contrasena))

    def comprimir(
        self, documento_id: str, destino: Path, progreso: Progreso | None = None
    ) -> ResultadoCompresion:
        if progreso is not None:
            progreso(1, 1)
        self.compresiones.append((documento_id, destino))
        return self.resultado_compresion

    def exportar_png(
        self,
        documento_id: str,
        directorio: Path,
        dpi: int,
        progreso: Progreso | None = None,
    ) -> list[Path]:
        if progreso is not None:
            progreso(1, 1)
        self.exportaciones_png.append((documento_id, directorio, dpi))
        return self.rutas_png

    def exportar_texto(self, documento_id: str, destino: Path) -> None:
        self.exportaciones_texto.append((documento_id, destino))


class FakeServicioBusqueda:
    """Fake en memoria de `ServicioBusqueda`. Registra las llamadas."""

    def __init__(self, coincidencias: tuple[Coincidencia, ...] = ()) -> None:
        self._coincidencias = coincidencias
        self.llamadas: list[tuple[str, str, bool]] = []

    def buscar(
        self,
        documento_id: str,
        termino: str,
        coincidir_mayusculas: bool = False,
        progreso: Progreso | None = None,
    ) -> tuple[Coincidencia, ...]:
        if progreso is not None:
            progreso(1, 1)
        self.llamadas.append((documento_id, termino, coincidir_mayusculas))
        return self._coincidencias


class FakeConversorPDF:
    """Fake en memoria de `ConversorPDF`. Registra las llamadas."""

    def __init__(self, escaneado: bool = False) -> None:
        self._escaneado = escaneado
        self.word: list[tuple[str, Path, Rango | None]] = []
        self.html: list[tuple[str, Path, Rango | None, bool]] = []
        self.markdown: list[tuple[str, Path, Rango | None]] = []

    def a_word(self, documento_id, destino, rango=None, progreso=None):  # type: ignore[no-untyped-def]
        if progreso is not None:
            progreso(1, 1)
        self.word.append((documento_id, destino, rango))

    def a_html(self, documento_id, destino, rango=None, imagenes_embebidas=True, progreso=None):  # type: ignore[no-untyped-def]
        if progreso is not None:
            progreso(1, 1)
        self.html.append((documento_id, destino, rango, imagenes_embebidas))

    def a_markdown(self, documento_id, destino, rango=None, progreso=None):  # type: ignore[no-untyped-def]
        if progreso is not None:
            progreso(1, 1)
        self.markdown.append((documento_id, destino, rango))

    def es_escaneado(self, documento_id: str) -> bool:
        return self._escaneado


class FakeConversorWord:
    """Fake en memoria de `ConversorWord`. Registra las conversiones."""

    def __init__(self) -> None:
        self.conversiones: list[tuple[Path, Path]] = []

    def a_pdf(self, ruta_docx, destino, config, progreso=None):  # type: ignore[no-untyped-def]
        if progreso is not None:
            progreso(1, 1)
        self.conversiones.append((ruta_docx, destino))
