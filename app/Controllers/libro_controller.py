"""Endpoints HTTP de libros, stock y autores asociados."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlmodel import Session

from app.database import get_session
from app.Models import LibroCreate, LibroRead, LibroUpdate
from app.security import requiere_bibliotecario
from app.Service import libro_service

router = APIRouter(
    prefix="/libros",
    tags=["Libros"],
    dependencies=[Depends(requiere_bibliotecario)],
)


@router.get("", response_model=list[LibroRead])
def listar_libros(
    disponibles: bool | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[LibroRead]:
    return libro_service.listar(session, disponibles=disponibles)


@router.get("/{libro_id}", response_model=LibroRead)
def obtener_libro(libro_id: int, session: Session = Depends(get_session)) -> LibroRead:
    return libro_service.obtener(session, libro_id)


@router.post("", response_model=LibroRead, status_code=status.HTTP_201_CREATED)
def crear_libro(
    datos: LibroCreate, session: Session = Depends(get_session)
) -> LibroRead:
    return libro_service.crear(session, datos)


@router.put("/{libro_id}", response_model=LibroRead)
def actualizar_libro(
    libro_id: int, datos: LibroUpdate, session: Session = Depends(get_session)
) -> LibroRead:
    return libro_service.actualizar(session, libro_id, datos)


@router.delete("/{libro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_libro(libro_id: int, session: Session = Depends(get_session)) -> Response:
    libro_service.eliminar(session, libro_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{libro_id}/autores/{autor_id}", response_model=LibroRead)
def asociar_autor(
    libro_id: int, autor_id: int, session: Session = Depends(get_session)
) -> LibroRead:
    return libro_service.asociar_autor(session, libro_id, autor_id)


@router.delete(
    "/{libro_id}/autores/{autor_id}", status_code=status.HTTP_204_NO_CONTENT
)
def desasociar_autor(
    libro_id: int, autor_id: int, session: Session = Depends(get_session)
) -> Response:
    libro_service.desasociar_autor(session, libro_id, autor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
