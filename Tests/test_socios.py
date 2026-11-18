"""Tests del CRUD de socios, unicidad de email y permisos del rol socio."""

import uuid


def test_crud_socio(client, headers_bibliotecario):
    email = f"{uuid.uuid4().hex[:8]}@test.com"
    respuesta = client.post(
        "/socios",
        json={"nombre": "Lucía Gómez", "email": email},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 201
    socio = respuesta.json()
    assert socio["activo"] is True

    respuesta = client.put(
        f"/socios/{socio['id']}",
        json={"activo": False},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["activo"] is False
    assert respuesta.json()["nombre"] == "Lucía Gómez"

    assert (
        client.get("/socios", headers=headers_bibliotecario).status_code == 200
    )
    assert (
        client.delete(
            f"/socios/{socio['id']}", headers=headers_bibliotecario
        ).status_code
        == 204
    )
    assert (
        client.get(f"/socios/{socio['id']}", headers=headers_bibliotecario).status_code
        == 404
    )


def test_email_duplicado_da_409(client, headers_bibliotecario, crear_socio):
    socio = crear_socio()

    respuesta = client.post(
        "/socios",
        json={"nombre": "Otro", "email": socio["email"]},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 409
    assert "email" in respuesta.json()["detail"]

    otro = crear_socio()
    respuesta = client.put(
        f"/socios/{otro['id']}",
        json={"email": socio["email"]},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 409


def test_socio_inexistente_da_404(client, headers_bibliotecario):
    assert client.get("/socios/999", headers=headers_bibliotecario).status_code == 404
    assert (
        client.put(
            "/socios/999", json={"nombre": "X"}, headers=headers_bibliotecario
        ).status_code
        == 404
    )
    assert (
        client.delete("/socios/999", headers=headers_bibliotecario).status_code == 404
    )


def test_filtro_activos(client, headers_bibliotecario, crear_socio):
    activo = crear_socio(nombre="Activo")
    inactivo = crear_socio(nombre="Inactivo")
    client.put(
        f"/socios/{inactivo['id']}",
        json={"activo": False},
        headers=headers_bibliotecario,
    )

    respuesta = client.get("/socios?activos=true", headers=headers_bibliotecario)
    assert [s["id"] for s in respuesta.json()] == [activo["id"]]

    respuesta = client.get("/socios?activos=false", headers=headers_bibliotecario)
    assert [s["id"] for s in respuesta.json()] == [inactivo["id"]]


def test_no_se_borra_socio_con_prestamos(
    client, headers_bibliotecario, crear_socio, crear_libro, crear_prestamo
):
    socio = crear_socio()
    libro = crear_libro(stock=1)
    crear_prestamo(socio["id"], libro["id"])

    respuesta = client.delete(
        f"/socios/{socio['id']}", headers=headers_bibliotecario
    )
    assert respuesta.status_code == 409


def test_socio_solo_ve_sus_propios_prestamos(
    client,
    headers_bibliotecario,
    headers_socio,
    socio,
    crear_socio,
    crear_libro,
    crear_prestamo,
):
    libro = crear_libro(stock=2)
    crear_prestamo(socio["id"], libro["id"])
    otro_socio = crear_socio()

    respuesta = client.get(
        f"/socios/{socio['id']}/prestamos", headers=headers_socio
    )
    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1

    respuesta = client.get(
        f"/socios/{otro_socio['id']}/prestamos", headers=headers_socio
    )
    assert respuesta.status_code == 403


def test_socio_no_puede_administrar_catalogo(
    client, headers_socio, crear_autor, crear_libro
):
    assert client.get("/libros", headers=headers_socio).status_code == 403
    assert client.get("/autores", headers=headers_socio).status_code == 403
    assert client.get("/socios", headers=headers_socio).status_code == 403
    assert (
        client.post(
            "/autores",
            json={"nombre": "X", "nacionalidad": "Y"},
            headers=headers_socio,
        ).status_code
        == 403
    )
