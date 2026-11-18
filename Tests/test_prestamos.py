"""Tests de préstamos: stock, límite, socio inactivo, plazos y multas."""

from datetime import date, timedelta

from sqlmodel import select

from app.Models import Prestamo


def test_crear_prestamo_calcula_vencimiento_y_descuenta_stock(
    client, headers_bibliotecario, crear_libro, crear_socio
):
    libro = crear_libro(stock=3)
    socio = crear_socio()

    respuesta = client.post(
        "/prestamos",
        json={"socio_id": socio["id"], "libro_id": libro["id"]},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 201
    prestamo = respuesta.json()

    assert prestamo["fecha_prestamo"] == date.today().isoformat()
    assert (
        date.fromisoformat(prestamo["fecha_vencimiento"])
        == date.today() + timedelta(days=14)
    )
    assert prestamo["fecha_devolucion"] is None
    assert prestamo["multa"] == 0
    assert prestamo["socio_nombre"] == socio["nombre"]
    assert prestamo["libro_titulo"] == libro["titulo"]

    libro = client.get(f"/libros/{libro['id']}", headers=headers_bibliotecario).json()
    assert libro["stock"] == 2


def test_no_se_presta_sin_stock(
    client, headers_bibliotecario, crear_libro, crear_socio
):
    libro = crear_libro(stock=0)
    socio = crear_socio()

    respuesta = client.post(
        "/prestamos",
        json={"socio_id": socio["id"], "libro_id": libro["id"]},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 409
    assert "stock" in respuesta.json()["detail"].lower()


def test_socio_inactivo_no_puede_pedir_prestamos(
    client, headers_bibliotecario, crear_libro, crear_socio
):
    libro = crear_libro(stock=1)
    socio = crear_socio()
    client.put(
        f"/socios/{socio['id']}",
        json={"activo": False},
        headers=headers_bibliotecario,
    )

    respuesta = client.post(
        "/prestamos",
        json={"socio_id": socio["id"], "libro_id": libro["id"]},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 403

    libro = client.get(f"/libros/{libro['id']}", headers=headers_bibliotecario).json()
    assert libro["stock"] == 1  # no se descontó nada


def test_limite_de_tres_prestamos_activos(
    client, headers_bibliotecario, crear_libro, crear_socio, crear_prestamo
):
    libro = crear_libro(stock=4)
    socio = crear_socio()

    for _ in range(3):
        crear_prestamo(socio["id"], libro["id"])

    respuesta = client.post(
        "/prestamos",
        json={"socio_id": socio["id"], "libro_id": libro["id"]},
        headers=headers_bibliotecario,
    )
    assert respuesta.status_code == 409
    assert "3" in respuesta.json()["detail"]

    libro = client.get(f"/libros/{libro['id']}", headers=headers_bibliotecario).json()
    assert libro["stock"] == 1


def test_prestamo_con_socio_o_libro_inexistente_da_404(
    client, headers_bibliotecario, crear_libro, crear_socio
):
    libro = crear_libro(stock=1)
    socio = crear_socio()

    assert (
        client.post(
            "/prestamos",
            json={"socio_id": 999, "libro_id": libro["id"]},
            headers=headers_bibliotecario,
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/prestamos",
            json={"socio_id": socio["id"], "libro_id": 999},
            headers=headers_bibliotecario,
        ).status_code
        == 404
    )
    assert (
        client.get("/prestamos/999", headers=headers_bibliotecario).status_code == 404
    )
    assert (
        client.post(
            "/prestamos/999/devolucion", headers=headers_bibliotecario
        ).status_code
        == 404
    )


def test_devolucion_a_tiempo_no_genera_multa(
    client, headers_bibliotecario, crear_libro, crear_socio, crear_prestamo
):
    libro = crear_libro(stock=1)
    socio = crear_socio()
    prestamo = crear_prestamo(socio["id"], libro["id"])

    respuesta = client.post(
        f"/prestamos/{prestamo['id']}/devolucion", headers=headers_bibliotecario
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["multa"] == 0
    assert respuesta.json()["fecha_devolucion"] == date.today().isoformat()

    libro = client.get(f"/libros/{libro['id']}", headers=headers_bibliotecario).json()
    assert libro["stock"] == 1


def test_devolucion_con_atraso_cobra_100_por_dia(
    client, headers_bibliotecario, crear_libro, crear_socio, crear_prestamo, session
):
    libro = crear_libro(stock=1)
    socio = crear_socio()
    prestamo = crear_prestamo(socio["id"], libro["id"])

    registro = session.get(Prestamo, prestamo["id"])
    registro.fecha_vencimiento = date.today() - timedelta(days=3)
    session.add(registro)
    session.commit()

    respuesta = client.post(
        f"/prestamos/{prestamo['id']}/devolucion", headers=headers_bibliotecario
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["multa"] == 300


def test_no_se_puede_devolver_dos_veces(
    client, headers_bibliotecario, crear_libro, crear_socio, crear_prestamo
):
    libro = crear_libro(stock=1)
    socio = crear_socio()
    prestamo = crear_prestamo(socio["id"], libro["id"])

    assert (
        client.post(
            f"/prestamos/{prestamo['id']}/devolucion", headers=headers_bibliotecario
        ).status_code
        == 200
    )
    respuesta = client.post(
        f"/prestamos/{prestamo['id']}/devolucion", headers=headers_bibliotecario
    )
    assert respuesta.status_code == 409

    libro = client.get(f"/libros/{libro['id']}", headers=headers_bibliotecario).json()
    assert libro["stock"] == 1  # no se repuso dos veces


def test_filtros_de_listado(
    client, headers_bibliotecario, crear_libro, crear_socio, crear_prestamo
):
    libro = crear_libro(stock=2)
    socio = crear_socio()
    activo = crear_prestamo(socio["id"], libro["id"])
    devuelto = crear_prestamo(socio["id"], libro["id"])
    client.post(
        f"/prestamos/{devuelto['id']}/devolucion", headers=headers_bibliotecario
    )

    activos = client.get(
        "/prestamos?activos=true", headers=headers_bibliotecario
    ).json()
    assert [p["id"] for p in activos] == [activo["id"]]

    devueltos = client.get(
        "/prestamos?activos=false", headers=headers_bibliotecario
    ).json()
    assert [p["id"] for p in devueltos] == [devuelto["id"]]

    del_socio = client.get(
        f"/prestamos?socio_id={socio['id']}", headers=headers_bibliotecario
    ).json()
    assert len(del_socio) == 2

    activos_socio = client.get(
        f"/socios/{socio['id']}/prestamos?activos=true",
        headers=headers_bibliotecario,
    ).json()
    assert [p["id"] for p in activos_socio] == [activo["id"]]


def test_prestamos_de_socio_inexistente_da_404(client, headers_bibliotecario):
    respuesta = client.get(
        "/socios/999/prestamos", headers=headers_bibliotecario
    )
    assert respuesta.status_code == 404


def test_prestamo_activo_se_identifica_por_fecha_devolucion(
    client, headers_bibliotecario, crear_libro, crear_socio, crear_prestamo, session
):
    libro = crear_libro(stock=2)
    socio = crear_socio()
    crear_prestamo(socio["id"], libro["id"])

    activos = session.exec(
        select(Prestamo).where(Prestamo.fecha_devolucion.is_(None))
    ).all()
    assert len(activos) == 1
