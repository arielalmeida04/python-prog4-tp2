"""Tests del CRUD de autores."""

def test_crud_autor(client, headers_bibliotecario):
    respuesta = client.post(
        "/autores",
        json={"nombre": "Borges", "nacionalidad": "Argentina"},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 201
    autor = respuesta.json()
    assert autor["id"] > 0

    respuesta = client.get("/autores", headers=headers_bibliotecario)
    assert respuesta.status_code == 200
    assert [a["nombre"] for a in respuesta.json()] == ["Borges"]

    respuesta = client.put(
        f"/autores/{autor['id']}",
        json={"nombre": "Jorge Luis Borges"},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Jorge Luis Borges"
    assert respuesta.json()["nacionalidad"] == "Argentina"

    respuesta = client.delete(
        f"/autores/{autor['id']}", headers=headers_bibliotecario
    )
    assert respuesta.status_code == 204

    respuesta = client.get(f"/autores/{autor['id']}", headers=headers_bibliotecario)
    assert respuesta.status_code == 404


def test_autor_inexistente_da_404(client, headers_bibliotecario):
    assert (
        client.get("/autores/999", headers=headers_bibliotecario).status_code == 404
    )
    assert (
        client.put(
            "/autores/999",
            json={"nombre": "X"},
            headers=headers_bibliotecario,
        ).status_code
        == 404
    )
    assert (
        client.delete("/autores/999", headers=headers_bibliotecario).status_code == 404
    )


def test_nombre_vacio_da_422(client, headers_bibliotecario):
    respuesta = client.post(
        "/autores",
        json={"nombre": "", "nacionalidad": "Argentina"},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 422


def test_eliminar_autor_lo_desasocia_de_sus_libros(
    client, headers_bibliotecario, crear_autor, crear_libro
):
    autor = crear_autor()
    libro = crear_libro()

    respuesta = client.post(
        f"/libros/{libro['id']}/autores/{autor['id']}",
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 200
    assert [a["id"] for a in respuesta.json()["autores"]] == [autor["id"]]

    assert (
        client.delete(
            f"/autores/{autor['id']}", headers=headers_bibliotecario
        ).status_code
        == 204
    )

    libro = client.get(
        f"/libros/{libro['id']}", headers=headers_bibliotecario
    ).json()
    assert libro["autores"] == []
