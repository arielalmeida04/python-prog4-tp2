"""Lógica de autenticación y administración de usuarios."""

from sqlmodel import Session, select

from app.Models import (
    ROLES_VALIDOS,
    Socio,
    Usuario,
    UsuarioCreate,
    UsuarioRead,
)
from app.errors import Conflicto, DatosInvalidos, NoAutorizado, NoEncontrado
from app.security import hashear_password, verificar_password


def autenticar(session: Session, email: str, password: str) -> Usuario:
    usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()
    if usuario is None or not verificar_password(password, usuario.password_hash):
        raise NoAutorizado("Credenciales inválidas")
    return usuario


def crear_usuario(session: Session, datos: UsuarioCreate) -> UsuarioRead:
    if datos.rol not in ROLES_VALIDOS:
        raise DatosInvalidos(
            f"Rol inválido: debe ser uno de {', '.join(ROLES_VALIDOS)}"
        )
    if datos.rol == "socio":
        if datos.socio_id is None:
            raise DatosInvalidos("Un usuario con rol socio debe tener socio_id")
        if session.get(Socio, datos.socio_id) is None:
            raise NoEncontrado(f"No existe el socio con id {datos.socio_id}")
    if session.exec(select(Usuario).where(Usuario.email == datos.email)).first():
        raise Conflicto("Ya existe un usuario con ese email")

    usuario = Usuario(
        email=datos.email,
        password_hash=hashear_password(datos.password),
        rol=datos.rol,
        socio_id=datos.socio_id,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return UsuarioRead.model_validate(usuario)
