"""Errores de dominio.

Los services lanzan estas excepciones (sin conocer FastAPI) y `main.py` las
traduce al código HTTP correspondiente.
"""


class ErrorDeDominio(Exception):
    """Error de negocio con código HTTP asociado."""

    status_code = 400

    def __init__(self, detalle: str) -> None:
        self.detalle = detalle
        super().__init__(detalle)


class DatosInvalidos(ErrorDeDominio):
    status_code = 422


class NoEncontrado(ErrorDeDominio):
    status_code = 404


class Conflicto(ErrorDeDominio):
    status_code = 409


class Prohibido(ErrorDeDominio):
    status_code = 403


class NoAutorizado(ErrorDeDominio):
    status_code = 401
