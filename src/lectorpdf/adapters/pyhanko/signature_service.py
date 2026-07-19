"""Adaptador de `SignatureService` sobre pyHanko.

pyHanko no trabaja sobre `fitz.Document`: solo ve rutas/bytes, que obtiene del
`RegistroDocumentos` compartido. Firmar sigue el flujo confirmado:
    guardar incremental a disco -> firmar la ruta (atómico) -> recargar(id).
La firma es una revisión incremental final, así que cubre todo lo anterior
(formularios y estampados incluidos) y preserva revisiones previas.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.fields import SigSeedSubFilter

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
)


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
        meta = signers.PdfSignatureMetadata(
            field_name=f"Firma_{uuid.uuid4().hex[:8]}",
            subfilter=SigSeedSubFilter.PADES,
            reason=config.razon,
        )

        # El registro vuelca los cambios pendientes, suelta el handle de fitz,
        # deja que pyHanko firme la ruta y reabre bajo el mismo id (marca FIRMADO).
        self._registro.reescribir_en_disco(
            documento_id, lambda ruta: self._firmar_fichero(ruta, meta, firmante)
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
    ) -> None:
        descriptor, temporal = tempfile.mkstemp(dir=str(ruta.parent), suffix=".pdf")
        os.close(descriptor)
        temporal_path = Path(temporal)
        try:
            with open(ruta, "rb") as entrada:
                escritor = IncrementalPdfFileWriter(entrada)
                with open(temporal_path, "wb") as salida:
                    signers.sign_pdf(escritor, meta, signer=firmante, output=salida)
            os.replace(temporal_path, ruta)
        except Exception as exc:
            temporal_path.unlink(missing_ok=True)
            raise ErrorDeFirma(f"No se pudo firmar el documento: {exc}") from exc
