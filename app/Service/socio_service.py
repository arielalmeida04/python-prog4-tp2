"""Lógica de negocio de socios."""

from sqlalchemy import func
from sqlmodel import Session, select

from app.Models import Prestamo, Socio, SocioCreate, SocioRead, SocioUpdate
from app.errors import Conflicto, NoEncontrado

MENSAJE_EMAIL_DUPLICADO = "Ya existe un socio con ese email"


def _a_read(socio: Socio) -> SocioRead:
    return SocioRead.model_validate(socio)


def _validar_email_unico(
    session: Session, email: str, excluir_id: int | None = None
) -> None:
    consulta = select(Socio).where(Socio.email == email)
    if excluir_id is not None:
        consulta = consulta.where(Socio.id != excluir_id)
    if session.exec(consulta).first() is not None:
        raise Conflicto(MENSAJE_EMAIL_DUPLICADO)


def listar(session: Session, activos: bool | None = None) -> list[SocioRead]:
    consulta = select(Socio).order_by(Socio.nombre)
    if activos is not None:
        consulta = consulta.where(Socio.activo.is_(activos))
    return [_a_read(socio) for socio in session.exec(consulta).all()]


def obtener_entidad(session: Session, socio_id: int) -> Socio:
    socio = session.get(Socio, socio_id)
    if socio is None:
        raise NoEncontrado(f"No existe el socio con id {socio_id}")
    return socio


def obtener(session: Session, socio_id: int) -> SocioRead:
    return _a_read(obtener_entidad(session, socio_id))


def crear(session: Session, datos: SocioCreate) -> SocioRead:
    _validar_email_unico(session, datos.email)
    socio = Socio.model_validate(datos)
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return _a_read(socio)


def actualizar(session: Session, socio_id: int, datos: SocioUpdate) -> SocioRead:
    socio = obtener_entidad(session, socio_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "email" in cambios and cambios["email"] != socio.email:
        _validar_email_unico(session, cambios["email"], excluir_id=socio_id)
    for campo, valor in cambios.items():
        setattr(socio, campo, valor)
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return _a_read(socio)


def eliminar(session: Session, socio_id: int) -> None:
    """Borra el socio solo si no tiene préstamos registrados."""
    socio = obtener_entidad(session, socio_id)
    prestamos = session.exec(
        select(func.count()).select_from(Prestamo).where(Prestamo.socio_id == socio_id)
    ).one()
    if prestamos:
        raise Conflicto(
            "No se puede eliminar un socio con préstamos registrados"
        )
    session.delete(socio)
    session.commit()
