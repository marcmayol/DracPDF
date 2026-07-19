"""Adaptador de `SignatureService` sobre pyHanko.

pyHanko no trabaja sobre `fitz.Document`: solo ve rutas/bytes, que obtiene del
`RegistroDocumentos` compartido. Firmar sigue el flujo confirmado:
    guardar incremental a disco -> firmar la ruta (atómico) -> recargar(id).
La firma es una revisión incremental final, así que cubre todo lo anterior
(formularios y estampados incluidos) y preserva revisiones previas.
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
import uuid
from collections.abc import Sequence
from pathlib import Path

from asn1crypto import x509
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import fields, signers
from pyhanko.sign.fields import SigFieldSpec, SigSeedSubFilter
from pyhanko.sign.timestamps import HTTPTimeStamper
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext

from lectorpdf.adapters.pymupdf.registro import Marca, RegistroDocumentos
from lectorpdf.core.domain.errores import (
    CredencialInvalida,
    DocumentoFirmado,
    ErrorDeFirma,
)
from lectorpdf.core.domain.firma_digital import (
    ConfigFirma,
    CredencialFirma,
    CredencialPKCS12,
    EstadoFirma,
    ResultadoVerificacion,
)

# pyHanko registra con traceback las modificaciones sospechosas al verificar;
# se refleja en el estado, así que se baja el ruido de ese logger.
logging.getLogger("pyhanko.sign.diff_analysis").setLevel(logging.CRITICAL)


class PyHankoSignatureService:
    def __init__(self, registro: RegistroDocumentos) -> None:
        self._registro = registro

    def firmar(
        self,
        documento_id: str,
        config: ConfigFirma,
        credencial: CredencialFirma,
    ) -> None:
        if self._registro.tiene(documento_id, Marca.FIRMADO):
            raise DocumentoFirmado("El documento ya está firmado: no se puede refirmar")

        firmante = self._cargar_firmante(credencial)
        nombre_campo = f"Firma_{uuid.uuid4().hex[:8]}"
        meta = signers.PdfSignatureMetadata(
            field_name=nombre_campo,
            subfilter=SigSeedSubFilter.PADES,
            reason=config.razon,
        )
        # Sello visible: se calcula la caja en coords PDF (origen abajo) antes de
        # soltar el handle de fitz. pyHanko rellena el nombre del firmante y la
        # fecha en la apariencia por defecto del campo.
        spec = self._campo_visible(documento_id, config, nombre_campo)
        sellador = self._timestamper(config)

        # El registro vuelca los cambios pendientes, suelta el handle de fitz,
        # deja que pyHanko firme la ruta y reabre bajo el mismo id (marca FIRMADO).
        self._registro.reescribir_en_disco(
            documento_id,
            lambda ruta: self._firmar_fichero(ruta, meta, firmante, spec, sellador),
        )

    def verificar(
        self,
        documento_id: str,
        anclas_confianza: Sequence[Path],
    ) -> tuple[ResultadoVerificacion, ...]:
        datos = self._registro.bytes_en_disco(documento_id)
        anclas = [x509.Certificate.load(Path(a).read_bytes()) for a in anclas_confianza]
        resultados: list[ResultadoVerificacion] = []
        with io.BytesIO(datos) as flujo:
            lector = PdfFileReader(flujo)
            for firma in lector.embedded_signatures:
                resultados.append(self._verificar_una(firma, anclas))
        return tuple(resultados)

    def _verificar_una(
        self, firma: object, anclas: list[object]
    ) -> ResultadoVerificacion:
        contexto = ValidationContext(trust_roots=anclas)
        try:
            estado = validate_pdf_signature(firma, contexto)
        except Exception as exc:
            return ResultadoVerificacion(
                firmante="(desconocido)",
                estado=EstadoFirma.INVALIDA,
                cubre_todo_el_documento=False,
                sellada_en_tiempo=False,
                motivo=f"No se pudo validar la firma: {exc}",
            )

        cubre_todo = getattr(estado.coverage, "name", "") == "ENTIRE_FILE"
        firmante = _nombre_firmante(estado)
        sellada = estado.timestamp_validity is not None

        if not estado.intact or not estado.valid:
            tipo, motivo = (
                EstadoFirma.INVALIDA,
                "La firma no es íntegra: los bytes firmados no coinciden.",
            )
        elif not cubre_todo:
            tipo, motivo = (
                EstadoFirma.INVALIDA,
                "El documento se modificó tras la firma (la firma no lo cubre entero).",
            )
        elif estado.trusted:
            tipo, motivo = EstadoFirma.VALIDA, "Firma válida y de confianza."
        else:
            tipo, motivo = (
                EstadoFirma.DESCONOCIDA,
                "Firma íntegra, pero el firmante no es de confianza.",
            )
        return ResultadoVerificacion(firmante, tipo, cubre_todo, sellada, motivo)

    def _timestamper(self, config: ConfigFirma) -> HTTPTimeStamper | None:
        """Sellado de tiempo opcional. Devuelve None si la TSA está deshabilitada
        (los tests corren así, sin red)."""
        if not config.usar_tsa:
            return None
        if not config.url_tsa:
            raise ValueError("Se pidió sellado de tiempo pero falta la URL de la TSA")
        return HTTPTimeStamper(config.url_tsa)

    def _campo_visible(
        self, documento_id: str, config: ConfigFirma, nombre_campo: str
    ) -> SigFieldSpec | None:
        if config.rect_pt is None:
            return None
        alto = self._registro.alto_pagina_pt(documento_id, config.pagina)
        r = config.rect_pt
        caja = (r.x0, alto - r.y1, r.x1, alto - r.y0)  # arriba-izq -> abajo-izq
        return SigFieldSpec(
            sig_field_name=nombre_campo, box=caja, on_page=config.pagina
        )

    # -- Interno ------------------------------------------------------------

    def _cargar_firmante(self, credencial: CredencialFirma) -> signers.SimpleSigner:
        if not isinstance(credencial, CredencialPKCS12):
            raise CredencialInvalida("Tipo de credencial no soportado")
        try:
            firmante = signers.SimpleSigner.load_pkcs12(
                pfx_file=str(credencial.ruta),
                passphrase=credencial.contrasena.encode(),
            )
        except Exception as exc:
            raise CredencialInvalida(f"No se pudo cargar el certificado: {exc}") from exc
        if firmante is None:
            raise CredencialInvalida("Certificado o contraseña incorrectos")
        return firmante

    def _firmar_fichero(
        self,
        ruta: Path,
        meta: signers.PdfSignatureMetadata,
        firmante: signers.SimpleSigner,
        spec: SigFieldSpec | None,
        sellador: HTTPTimeStamper | None,
    ) -> None:
        descriptor, temporal = tempfile.mkstemp(dir=str(ruta.parent), suffix=".pdf")
        os.close(descriptor)
        temporal_path = Path(temporal)
        try:
            with open(ruta, "rb") as entrada:
                escritor = IncrementalPdfFileWriter(entrada)
                if spec is not None:
                    fields.append_signature_field(escritor, spec)
                with open(temporal_path, "wb") as salida:
                    signers.sign_pdf(
                        escritor,
                        meta,
                        signer=firmante,
                        timestamper=sellador,
                        output=salida,
                    )
            os.replace(temporal_path, ruta)
        except Exception as exc:
            temporal_path.unlink(missing_ok=True)
            raise ErrorDeFirma(f"No se pudo firmar el documento: {exc}") from exc


def _nombre_firmante(estado: object) -> str:
    cert = getattr(estado, "signing_cert", None)
    if cert is None:
        return "(desconocido)"
    nombre = cert.subject.native.get("common_name")
    return str(nombre) if nombre else str(cert.subject.human_friendly)
