"""Tests de autenticación, roles y administración de usuarios."""

from sqlmodel import Session

from app.Models import Usuario
from app.security import hashear_password


def _insertar_usuario(
    session: Session, email: str, password: str, rol: str = "bibliotecario", socio_id=None
) -> Usuario:
    usuario = Usuario(
        email=email,
        password_hash=hashear_password(password),
        rol=rol,
        socio_id=socio_id,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


def test_login_correcto_devuelve_token(client, session):
    _insertar_usuario(session, "jefa@test.com", "clave123")

    respuesta = client.post(
        "/auth/login", json={"email": "jefa@test.com", "password": "clave123"}
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["token_type"] == "bearer"
    assert datos["rol"] == "bibliotecario"
    assert datos["access_token"]


def test_login_con_password_incorrecta_da_401(client, session):
    _insertar_usuario(session, "jefa@test.com", "clave123")

    respuesta = client.post(
        "/auth/login", json={"email": "jefa@test.com", "password": "mala"}
    )
    assert respuesta.status_code == 401


def test_login_con_usuario_inexistente_da_401(client):
    respuesta = client.post(
        "/auth/login", json={"email": "nadie@test.com", "password": "clave123"}
    )
    assert respuesta.status_code == 401


def test_endpoint_sin_token_da_401(client):
    assert client.get("/autores").status_code == 401


def test_token_invalido_da_401(client):
    assert (
        client.get(
            "/autores", headers={"Authorization": "Bearer token-falso"}
        ).status_code
        == 401
    )
    assert (
        client.get(
            "/autores", headers={"Authorization": "Bearer basura.otra"}
        ).status_code
        == 401
    )


def test_bibliotecario_crea_usuario_socio_y_ese_usuario_hace_login(
    client, headers_bibliotecario, socio
):
    respuesta = client.post(
        "/auth/usuarios",
        json={
            "email": "nuevo@test.com",
            "password": "clave123",
            "rol": "socio",
            "socio_id": socio["id"],
        },
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["socio_id"] == socio["id"]
    assert "password_hash" not in respuesta.json()

    respuesta = client.post(
        "/auth/login", json={"email": "nuevo@test.com", "password": "clave123"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "socio"


def test_validaciones_al_crear_usuario(client, headers_bibliotecario, socio):
    email = "repetido@test.com"
    datos = {"email": email, "password": "clave123", "rol": "bibliotecario"}
    assert (
        client.post(
            "/auth/usuarios", json=datos, headers=headers_bibliotecario
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/auth/usuarios", json=datos, headers=headers_bibliotecario
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/auth/usuarios",
            json={"email": "otro@test.com", "password": "clave123", "rol": "admin"},
            headers=headers_bibliotecario,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/auth/usuarios",
            json={"email": "socio@test.com", "password": "clave123", "rol": "socio"},
            headers=headers_bibliotecario,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/auth/usuarios",
            json={
                "email": "socio2@test.com",
                "password": "clave123",
                "rol": "socio",
                "socio_id": 999,
            },
            headers=headers_bibliotecario,
        ).status_code
        == 404
    )


def test_socio_no_puede_crear_usuarios(client, headers_socio):
    respuesta = client.post(
        "/auth/usuarios",
        json={"email": "x@test.com", "password": "clave123", "rol": "socio"},
        headers=headers_socio,
    )
    assert respuesta.status_code == 403


def test_raiz_responde(client):
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert "documentacion" in respuesta.json()
