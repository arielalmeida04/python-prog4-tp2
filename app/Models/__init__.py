"""Modelos de la base de datos y schemas de la API.

El orden de importación importa: primero la tabla intermedia y las entidades
sin dependencias, después las que las referencian.
"""

from app.Models.autor import Autor, AutorCreate, AutorRead, AutorUpdate
from app.Models.libro import Libro, LibroCreate, LibroRead, LibroUpdate
from app.Models.libro_autor import LibroAutor
from app.Models.prestamo import Prestamo, PrestamoCreate, PrestamoRead
from app.Models.socio import Socio, SocioCreate, SocioRead, SocioUpdate
from app.Models.usuario import (
    ROLES_VALIDOS,
    LoginRequest,
    TokenResponse,
    Usuario,
    UsuarioCreate,
    UsuarioRead,
)

__all__ = [
    "ROLES_VALIDOS",
    "Autor",
    "AutorCreate",
    "AutorRead",
    "AutorUpdate",
    "Libro",
    "LibroAutor",
    "LibroCreate",
    "LibroRead",
    "LibroUpdate",
    "LoginRequest",
    "Prestamo",
    "PrestamoCreate",
    "PrestamoRead",
    "Socio",
    "SocioCreate",
    "SocioRead",
    "SocioUpdate",
    "TokenResponse",
    "Usuario",
    "UsuarioCreate",
    "UsuarioRead",
]
