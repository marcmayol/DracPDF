"""Excepciones de dominio. Los adaptadores traducen sus errores a estas."""

from __future__ import annotations


class ErrorDominio(Exception):
    """Raíz de las excepciones de dominio de lectorpdf."""


class DocumentoNoEncontrado(ErrorDominio):
    """La ruta indicada no existe o no es un fichero."""


class FormatoNoSoportado(ErrorDominio):
    """El fichero no es un PDF válido o no se puede abrir como tal."""


class DocumentoNoAbierto(ErrorDominio):
    """Se referencia un documento cuyo id no está abierto en el repositorio."""


class PaginaFueraDeRango(ErrorDominio):
    """Se solicita una página con índice fuera de [0, num_paginas)."""


class FormularioXFANoSoportado(ErrorDominio):
    """El documento usa formularios XFA, no soportados (solo AcroForm)."""


class CampoNoEncontrado(ErrorDominio):
    """No existe ningún campo con el id indicado en el documento."""


class CampoSoloLectura(ErrorDominio):
    """Se intenta escribir en un campo marcado como de solo lectura."""


class ValorDeCampoInvalido(ErrorDominio):
    """El valor no es válido para el tipo de campo (p. ej. no está entre las opciones)."""


class DocumentoFirmado(ErrorDominio):
    """Se intenta editar un documento ya firmado (edición bloqueada)."""


class CredencialInvalida(ErrorDominio):
    """La credencial de firma no es válida (p. ej. el .p12 no existe)."""


class ErrorDeFirma(ErrorDominio):
    """Fallo al firmar criptográficamente el documento."""


class RangoInvalido(ErrorDominio):
    """Un rango de páginas está fuera de los límites del documento."""


class ContrasenaIncorrecta(ErrorDominio):
    """La contraseña no permite abrir/descifrar el documento."""


class SinPaginas(ErrorDominio):
    """La operación dejaría el documento sin páginas, o no hay entrada."""


class OperacionCancelada(ErrorDominio):
    """El usuario canceló una operación larga."""
