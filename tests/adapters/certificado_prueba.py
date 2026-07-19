"""Generación de un certificado PKCS#12 autofirmado de prueba.

No versionar el .p12: se genera al vuelo (por script o en los tests). Devuelve el
.p12 (clave + cert, protegido con contraseña) y el certificado público en DER
para usarlo como ancla de confianza al verificar.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    pkcs12,
)
from cryptography.x509.oid import NameOID

CONTRASENA_POR_DEFECTO = "prueba"
NOMBRE_POR_DEFECTO = "Firma de prueba lectorpdf"


def generar_pkcs12(
    directorio: Path,
    contrasena: str = CONTRASENA_POR_DEFECTO,
    nombre_comun: str = NOMBRE_POR_DEFECTO,
) -> tuple[Path, Path]:
    """Crea `cert.p12` y `cert.der` en `directorio`. Devuelve (p12, der)."""
    directorio.mkdir(parents=True, exist_ok=True)

    clave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, nombre_comun)])
    ahora = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(nombre)
        .issuer_name(nombre)
        .public_key(clave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - datetime.timedelta(days=1))
        .not_valid_after(ahora + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(clave, hashes.SHA256())
    )

    p12 = directorio / "cert.p12"
    der = directorio / "cert.der"
    p12.write_bytes(
        pkcs12.serialize_key_and_certificates(
            b"lectorpdf", clave, cert, None, BestAvailableEncryption(contrasena.encode())
        )
    )
    der.write_bytes(cert.public_bytes(Encoding.DER))
    return p12, der
