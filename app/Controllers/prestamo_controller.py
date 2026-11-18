"""Endpoints HTTP de préstamos y devoluciones."""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.database import get_session
from app.Models import PrestamoCreate, PrestamoRead
from app.security import requiere_bibliotecario
from app.Service import prestamo_service

router = APIRouter(
    prefix="/prestamos",
    tags=["Préstamos"],
    dependencies=[Depends(requiere_bibliotecario)],
)


@router.get("", response_model=list[PrestamoRead])
def listar_prestamos(
    activos: bool | None = Query(default=None),
    socio_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[PrestamoRead]:
    return prestamo_service.listar(session, activos=activos, socio_id=socio_id)


@router.get("/{prestamo_id}", response_model=PrestamoRead)
def obtener_prestamo(
    prestamo_id: int, session: Session = Depends(get_session)
) -> PrestamoRead:
    return prestamo_service.obtener(session, prestamo_id)


@router.post("", response_model=PrestamoRead, status_code=status.HTTP_201_CREATED)
def crear_prestamo(
    datos: PrestamoCreate, session: Session = Depends(get_session)
) -> PrestamoRead:
    return prestamo_service.crear(session, datos)


@router.post("/{prestamo_id}/devolucion", response_model=PrestamoRead)
def devolver_prestamo(
    prestamo_id: int, session: Session = Depends(get_session)
) -> PrestamoRead:
    return prestamo_service.devolver(session, prestamo_id)
