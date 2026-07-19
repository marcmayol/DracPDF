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
