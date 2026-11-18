"""Lógica de negocio de préstamos y devoluciones."""

from datetime import date, timedelta

from sqlalchemy import func, update
from sqlmodel import Session, select

from app.Models import (
    Libro,
    Prestamo,
    PrestamoCreate,
    PrestamoRead,
    Socio,
)
from app.errors import Conflicto, NoEncontrado, Prohibido
from app.Service import socio_service

PLAZO_DIAS = 14
MULTA_POR_DIA = 100.0
MAX_PRESTAMOS_ACTIVOS = 3


def _a_read(prestamo: Prestamo) -> PrestamoRead:
    return PrestamoRead(
        id=prestamo.id,
        socio_id=prestamo.socio_id,
        libro_id=prestamo.libro_id,
        fecha_prestamo=prestamo.fecha_prestamo,
        fecha_vencimiento=prestamo.fecha_vencimiento,
        fecha_devolucion=prestamo.fecha_devolucion,
        multa=prestamo.multa,
        socio_nombre=prestamo.socio.nombre if prestamo.socio else None,
        libro_titulo=prestamo.libro.titulo if prestamo.libro else None,
    )


def contar_activos(session: Session, socio_id: int) -> int:
    return session.exec(
        select(func.count())
        .select_from(Prestamo)
        .where(
            Prestamo.socio_id == socio_id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ).one()


def obtener_entidad(session: Session, prestamo_id: int) -> Prestamo:
    prestamo = session.get(Prestamo, prestamo_id)
    if prestamo is None:
        raise NoEncontrado(f"No existe el préstamo con id {prestamo_id}")
    return prestamo


def obtener(session: Session, prestamo_id: int) -> PrestamoRead:
    return _a_read(obtener_entidad(session, prestamo_id))


def listar(
    session: Session,
    activos: bool | None = None,
    socio_id: int | None = None,
) -> list[PrestamoRead]:
    consulta = select(Prestamo)
    if socio_id is not None:
        consulta = consulta.where(Prestamo.socio_id == socio_id)
    if activos is True:
        consulta = consulta.where(Prestamo.fecha_devolucion.is_(None))
    elif activos is False:
        consulta = consulta.where(Prestamo.fecha_devolucion.is_not(None))
    consulta = consulta.order_by(Prestamo.id)
    return [_a_read(prestamo) for prestamo in session.exec(consulta).all()]


def listar_por_socio(
    session: Session, socio_id: int, activos: bool | None = None
) -> list[PrestamoRead]:
    socio_service.obtener_entidad(session, socio_id)  # 404 si no existe
    return listar(session, activos=activos, socio_id=socio_id)


def crear(
    session: Session, datos: PrestamoCreate, hoy: date | None = None
) -> PrestamoRead:
    """Registra un préstamo aplicando todas las reglas de negocio."""
    socio = session.get(Socio, datos.socio_id)
    if socio is None:
        raise NoEncontrado(f"No existe el socio con id {datos.socio_id}")
    if not socio.activo:
        raise Prohibido("El socio está inactivo y no puede pedir préstamos")

    libro = session.get(Libro, datos.libro_id)
    if libro is None:
        raise NoEncontrado(f"No existe el libro con id {datos.libro_id}")

    if contar_activos(session, socio.id) >= MAX_PRESTAMOS_ACTIVOS:
        raise Conflicto(
            f"El socio ya tiene {MAX_PRESTAMOS_ACTIVOS} préstamos activos"
        )

    # UPDATE condicional: evita que dos requests simultáneos dejen stock negativo.
    resultado = session.execute(
        update(Libro)
        .where(Libro.id == libro.id, Libro.stock > 0)
        .values(stock=Libro.stock - 1)
    )
    if resultado.rowcount == 0:
        raise Conflicto("No hay stock disponible para ese libro")

    hoy = hoy or date.today()
    prestamo = Prestamo(
        socio_id=socio.id,
        libro_id=libro.id,
        fecha_prestamo=hoy,
        fecha_vencimiento=hoy + timedelta(days=PLAZO_DIAS),
        fecha_devolucion=None,
        multa=0.0,
    )
    session.add(prestamo)
    session.commit()
    session.refresh(prestamo)
    return _a_read(prestamo)


def devolver(
    session: Session, prestamo_id: int, hoy: date | None = None
) -> PrestamoRead:
    """Registra la devolución: repone stock y calcula la multa por atraso."""
    prestamo = obtener_entidad(session, prestamo_id)
    if prestamo.fecha_devolucion is not None:
        raise Conflicto("El préstamo ya fue devuelto")

    hoy = hoy or date.today()
    dias_de_atraso = max(0, (hoy - prestamo.fecha_vencimiento).days)
    prestamo.fecha_devolucion = hoy
    prestamo.multa = float(dias_de_atraso * MULTA_POR_DIA)

    libro = session.get(Libro, prestamo.libro_id)
    if libro is not None:
        libro.stock += 1
        session.add(libro)

    session.add(prestamo)
    session.commit()
    session.refresh(prestamo)
    return _a_read(prestamo)
