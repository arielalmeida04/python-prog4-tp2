"""Tests del CRUD de libros, stock, filtro y relación N-N con autores."""

import uuid


def test_crud_libro(client, headers_bibliotecario):
    isbn = f"978-{uuid.uuid4().hex[:10]}"
    respuesta = client.post(
        "/libros",
        json={"titulo": "Ficciones", "isbn": isbn, "stock": 2, "anio": 1944},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 201
    libro = respuesta.json()
    assert libro["stock"] == 2
    assert libro["autores"] == []

    respuesta = client.put(
        f"/libros/{libro['id']}",
        json={"stock": 5},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["stock"] == 5
    assert respuesta.json()["titulo"] == "Ficciones"

    assert (
        client.delete(
            f"/libros/{libro['id']}", headers=headers_bibliotecario
        ).status_code
        == 204
    )
    assert (
        client.get(f"/libros/{libro['id']}", headers=headers_bibliotecario).status_code
        == 404
    )


def test_isbn_duplicado_da_409(client, headers_bibliotecario, crear_libro):
    libro = crear_libro(isbn="978-UNICO")

    respuesta = client.post(
        "/libros",
        json={"titulo": "Otro", "isbn": "978-UNICO", "stock": 1, "anio": 2000},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 409
    assert "ISBN" in respuesta.json()["detail"]

    otro = crear_libro(isbn="978-OTRO")
    respuesta = client.put(
        f"/libros/{otro['id']}", json={"isbn": "978-UNICO"}, headers=headers_bibliotecario
    )
    assert respuesta.status_code == 409

    # Guardar el mismo ISBN que ya tiene el propio libro es válido.
    respuesta = client.put(
        f"/libros/{libro['id']}", json={"isbn": "978-UNICO"}, headers=headers_bibliotecario
    )
    assert respuesta.status_code == 200


def test_filtro_disponibles(client, headers_bibliotecario, crear_libro):
    crear_libro(titulo="Sin stock", stock=0)
    crear_libro(titulo="Con stock", stock=3)

    respuesta = client.get(
        "/libros?disponibles=true", headers=headers_bibliotecario
    )
    assert respuesta.status_code == 200
    titulos = [libro["titulo"] for libro in respuesta.json()]
    assert titulos == ["Con stock"]

    assert len(client.get("/libros", headers=headers_bibliotecario).json()) == 2


def test_asociar_y_desasociar_autores(
    client, headers_bibliotecario, crear_libro, crear_autor
):
    libro = crear_libro()
    autor = crear_autor()

    respuesta = client.post(
        f"/libros/{libro['id']}/autores/{autor['id']}",
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 200
    assert [a["nombre"] for a in respuesta.json()["autores"]] == [autor["nombre"]]

    # Asociar dos veces no duplica la relación.
    respuesta = client.post(
        f"/libros/{libro['id']}/autores/{autor['id']}",
        headers=headers_bibliotecario,
    )
    assert len(respuesta.json()["autores"]) == 1

    respuesta = client.delete(
        f"/libros/{libro['id']}/autores/{autor['id']}",
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 204

    libro = client.get(
        f"/libros/{libro['id']}", headers=headers_bibliotecario
    ).json()
    assert libro["autores"] == []


def test_asociar_con_inexistentes_da_404(
    client, headers_bibliotecario, crear_libro, crear_autor
):
    libro = crear_libro()
    autor = crear_autor()

    assert (
        client.post(
            f"/libros/999/autores/{autor['id']}", headers=headers_bibliotecario
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/libros/{libro['id']}/autores/999", headers=headers_bibliotecario
        ).status_code
        == 404
    )


def test_desasociar_autor_no_asociado_da_409(
    client, headers_bibliotecario, crear_libro, crear_autor
):
    libro = crear_libro()
    autor = crear_autor()

    respuesta = client.delete(
        f"/libros/{libro['id']}/autores/{autor['id']}",
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 409


def test_stock_negativo_da_422(client, headers_bibliotecario):
    respuesta = client.post(
        "/libros",
        json={"titulo": "X", "isbn": "978-NEG", "stock": -1, "anio": 2020},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 422


def test_no_se_borra_libro_con_prestamos(
    client, headers_bibliotecario, crear_libro, crear_socio, crear_prestamo
):
    libro = crear_libro(stock=1)
    socio = crear_socio()
    crear_prestamo(socio["id"], libro["id"])

    respuesta = client.delete(
        f"/libros/{libro['id']}", headers=headers_bibliotecario
    )
    assert respuesta.status_code == 409
