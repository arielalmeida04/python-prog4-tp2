"""Aplicación FastAPI: routers, manejadores de error y arranque de la BD."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.Controllers import (
    auth_controller,
    autor_controller,
    libro_controller,
    prestamo_controller,
    socio_controller,
)
from app.database import crear_tablas
from app.errors import ErrorDeDominio


@asynccontextmanager
async def lifespan(_app: FastAPI):
    crear_tablas()
    yield


app = FastAPI(
    title="Biblioteca",
    version="1.0.0",
    description=(
        "API REST para gestionar el catálogo de una biblioteca, sus socios "
        "y los préstamos. Autenticación con token Bearer (`POST /auth/login`)."
    ),
    lifespan=lifespan,
)


@app.exception_handler(ErrorDeDominio)
async def manejar_error_de_dominio(
    _request: Request, exc: ErrorDeDominio
) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detalle})


@app.exception_handler(IntegrityError)
async def manejar_error_de_integridad(
    _request: Request, _exc: IntegrityError
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "La operación entra en conflicto con datos existentes"},
    )


@app.get("/", include_in_schema=False)
def raiz() -> dict[str, str]:
    return {"mensaje": "API de la biblioteca", "documentacion": "/docs"}


app.include_router(auth_controller.router)
app.include_router(autor_controller.router)
app.include_router(libro_controller.router)
app.include_router(socio_controller.router)
app.include_router(prestamo_controller.router)
