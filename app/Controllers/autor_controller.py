"""Endpoints HTTP de autores. Solo delegan en la capa de servicios."""

from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from app.database import get_session
from app.Models import AutorCreate, AutorRead, AutorUpdate
from app.security import requiere_bibliotecario
from app.Service import autor_service

router = APIRouter(
    prefix="/autores",
    tags=["Autores"],
    dependencies=[Depends(requiere_bibliotecario)],
)


@router.get("", response_model=list[AutorRead])
def listar_autores(session: Session = Depends(get_session)) -> list[AutorRead]:
    return autor_service.listar(session)


@router.get("/{autor_id}", response_model=AutorRead)
def obtener_autor(autor_id: int, session: Session = Depends(get_session)) -> AutorRead:
    return autor_service.obtener(session, autor_id)


@router.post("", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
def crear_autor(
    datos: AutorCreate, session: Session = Depends(get_session)
) -> AutorRead:
    return autor_service.crear(session, datos)


@router.put("/{autor_id}", response_model=AutorRead)
def actualizar_autor(
    autor_id: int, datos: AutorUpdate, session: Session = Depends(get_session)
) -> AutorRead:
    return autor_service.actualizar(session, autor_id, datos)


@router.delete("/{autor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_autor(autor_id: int, session: Session = Depends(get_session)) -> Response:
    autor_service.eliminar(session, autor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
