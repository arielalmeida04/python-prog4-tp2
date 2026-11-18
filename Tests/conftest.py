"""Fixtures compartidas: base en memoria, cliente HTTP y usuarios autenticados."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

from app.database import crear_engine, get_session
from app.main import app
from app.Models import Usuario
from app.security import crear_token, hashear_password

engine_prueba = crear_engine("sqlite://", poolclass=StaticPool)


def _sesion_de_prueba():
    with Session(engine_prueba, expire_on_commit=False) as session:
        yield session


# Cada request de la API usa la base en memoria en lugar de biblioteca.db.
app.dependency_overrides[get_session] = _sesion_de_prueba


@pytest.fixture(autouse=True)
def base_limpia():
    SQLModel.metadata.create_all(engine_prueba)
    yield
    SQLModel.metadata.drop_all(engine_prueba)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session():
    with Session(engine_prueba, expire_on_commit=False) as session:
        yield session


def _crear_usuario(
    session: Session, email: str, rol: str, socio_id: int | None = None
) -> Usuario:
    usuario = Usuario(
        email=email,
        password_hash=hashear_password("secreto123"),
        rol=rol,
        socio_id=socio_id,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@pytest.fixture
def headers_bibliotecario(session):
    usuario = _crear_usuario(session, "biblio@test.com", "bibliotecario")
    return {"Authorization": f"Bearer {crear_token(usuario.id)}"}


@pytest.fixture
def socio(client, headers_bibliotecario):
    respuesta = client.post(
        "/socios",
        json={"nombre": "Ana Pérez", "email": "ana@test.com"},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 201
    return respuesta.json()


@pytest.fixture
def headers_socio(session, socio):
    usuario = _crear_usuario(session, "ana@test.com", "socio", socio["id"])
    return {"Authorization": f"Bearer {crear_token(usuario.id)}"}


@pytest.fixture
def crear_autor(client, headers_bibliotecario):
    def _crear(nombre: str = "Jorge Luis Borges", nacionalidad: str = "Argentina"):
        respuesta = client.post(
            "/autores",
            json={"nombre": nombre, "nacionalidad": nacionalidad},
            headers=headers_bibliotecario,
        )
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _crear


@pytest.fixture
def crear_libro(client, headers_bibliotecario):
    def _crear(
        titulo: str = "El Aleph",
        isbn: str | None = None,
        stock: int = 1,
        anio: int = 1949,
    ):
        respuesta = client.post(
            "/libros",
            json={
                "titulo": titulo,
                "isbn": isbn or f"978-{uuid.uuid4().hex[:10]}",
                "stock": stock,
                "anio": anio,
            },
            headers=headers_bibliotecario,
        )
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _crear


@pytest.fixture
def crear_socio(client, headers_bibliotecario):
    def _crear(nombre: str = "Carlos Ruiz", email: str | None = None):
        respuesta = client.post(
            "/socios",
            json={"nombre": nombre, "email": email or f"{uuid.uuid4().hex[:8]}@test.com"},
            headers=headers_bibliotecario,
        )
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _crear


@pytest.fixture
def crear_prestamo(client, headers_bibliotecario):
    def _crear(socio_id: int, libro_id: int):
        respuesta = client.post(
            "/prestamos",
            json={"socio_id": socio_id, "libro_id": libro_id},
            headers=headers_bibliotecario,
        )
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _crear
