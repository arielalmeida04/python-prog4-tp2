"""Endpoints HTTP de socios y de sus préstamos."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlmodel import Session

from app.database import get_session
from app.Models import (
    PrestamoRead,
    SocioCreate,
    SocioRead,
    SocioUpdate,
    Usuario,
)
from app.errors import Prohibido
from app.security import requiere_bibliotecario, usuario_actual
from app.Service import prestamo_service, socio_service

router = APIRouter(prefix="/socios", tags=["Socios"])


@router.get("", response_model=list[SocioRead])
def listar_socios(
    activos: bool | None = Query(default=None),
    session: Session = Depends(get_session),
    _: Usuario = Depends(requiere_bibliotecario),
) -> list[SocioRead]:
    return socio_service.listar(session, activos=activos)


@router.get("/{socio_id}", response_model=SocioRead)
def obtener_socio(
    socio_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(requiere_bibliotecario),
) -> SocioRead:
    return socio_service.obtener(session, socio_id)


@router.post(
    "", response_model=SocioRead, status_code=status.HTTP_201_CREATED
)
def crear_socio(
    datos: SocioCreate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(requiere_bibliotecario),
) -> SocioRead:
    return socio_service.crear(session, datos)


@router.put("/{socio_id}", response_model=SocioRead)
def actualizar_socio(
    socio_id: int,
    datos: SocioUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(requiere_bibliotecario),
) -> SocioRead:
    return socio_service.actualizar(session, socio_id, datos)


@router.delete("/{socio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_socio(
    socio_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(requiere_bibliotecario),
) -> Response:
    socio_service.eliminar(session, socio_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{socio_id}/prestamos", response_model=list[PrestamoRead])
def listar_prestamos_del_socio(
    socio_id: int,
    activos: bool | None = Query(default=None),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_actual),
) -> list[PrestamoRead]:
    """El bibliotecario ve cualquiera; un socio, solo los propios."""
    if usuario.rol == "socio" and usuario.socio_id != socio_id:
        raise Prohibido("Un socio solo puede consultar sus propios préstamos")
    return prestamo_service.listar_por_socio(session, socio_id, activos=activos)
