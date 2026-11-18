"""Endpoints de login y administración de usuarios."""

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database import get_session
from app.Models import LoginRequest, TokenResponse, UsuarioCreate, UsuarioRead
from app.security import crear_token, requiere_bibliotecario
from app.Service import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(
    datos: LoginRequest, session: Session = Depends(get_session)
) -> TokenResponse:
    usuario = auth_service.autenticar(session, datos.email, datos.password)
    return TokenResponse(
        access_token=crear_token(usuario.id), rol=usuario.rol
    )


@router.post(
    "/usuarios",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_bibliotecario)],
)
def crear_usuario(
    datos: UsuarioCreate, session: Session = Depends(get_session)
) -> UsuarioRead:
    return auth_service.crear_usuario(session, datos)
