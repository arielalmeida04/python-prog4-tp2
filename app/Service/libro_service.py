"""Lógica de negocio de libros, stock y relación N-N con autores."""

from sqlalchemy import delete, func
from sqlmodel import Session, select

from app.Models import (
    Autor,
    AutorRead,
    Libro,
    LibroAutor,
    LibroCreate,
    LibroRead,
    LibroUpdate,
    Prestamo,
)
from app.errors import Conflicto, NoEncontrado
from app.Service import autor_service

MENSAJE_ISBN_DUPLICADO = "Ya existe un libro con ese ISBN"


def _a_read(libro: Libro) -> LibroRead:
    return LibroRead(
        id=libro.id,
        titulo=libro.titulo,
        isbn=libro.isbn,
        stock=libro.stock,
        anio=libro.anio,
        autores=[AutorRead.model_validate(autor) for autor in libro.autores],
    )


def _validar_isbn_unico(
    session: Session, isbn: str, excluir_id: int | None = None
) -> None:
    consulta = select(Libro).where(Libro.isbn == isbn)
    if excluir_id is not None:
        consulta = consulta.where(Libro.id != excluir_id)
    if session.exec(consulta).first() is not None:
        raise Conflicto(MENSAJE_ISBN_DUPLICADO)


def listar(session: Session, disponibles: bool | None = None) -> list[LibroRead]:
    consulta = select(Libro).order_by(Libro.titulo)
    if disponibles:
        consulta = consulta.where(Libro.stock > 0)
    return [_a_read(libro) for libro in session.exec(consulta).all()]


def obtener_entidad(session: Session, libro_id: int) -> Libro:
    libro = session.get(Libro, libro_id)
    if libro is None:
        raise NoEncontrado(f"No existe el libro con id {libro_id}")
    return libro


def obtener(session: Session, libro_id: int) -> LibroRead:
    return _a_read(obtener_entidad(session, libro_id))


def crear(session: Session, datos: LibroCreate) -> LibroRead:
    _validar_isbn_unico(session, datos.isbn)
    libro = Libro.model_validate(datos)
    session.add(libro)
    session.commit()
    session.refresh(libro)
    return _a_read(libro)


def actualizar(session: Session, libro_id: int, datos: LibroUpdate) -> LibroRead:
    libro = obtener_entidad(session, libro_id)
    cambios = datos.model_dump(exclude_unset=True)
    if "isbn" in cambios and cambios["isbn"] != libro.isbn:
        _validar_isbn_unico(session, cambios["isbn"], excluir_id=libro_id)
    for campo, valor in cambios.items():
        setattr(libro, campo, valor)
    session.add(libro)
    session.commit()
    session.refresh(libro)
    return _a_read(libro)


def eliminar(session: Session, libro_id: int) -> None:
    """Borra el libro solo si no tiene préstamos (así no se pierde el historial)."""
    libro = obtener_entidad(session, libro_id)
    prestamos = session.exec(
        select(func.count()).select_from(Prestamo).where(Prestamo.libro_id == libro_id)
    ).one()
    if prestamos:
        raise Conflicto(
            "No se puede eliminar un libro con préstamos registrados"
        )
    session.execute(delete(LibroAutor).where(LibroAutor.libro_id == libro_id))
    session.delete(libro)
    session.commit()


def asociar_autor(session: Session, libro_id: int, autor_id: int) -> LibroRead:
    libro = obtener_entidad(session, libro_id)
    autor = autor_service.obtener_entidad(session, autor_id)
    if all(existente.id != autor.id for existente in libro.autores):
        libro.autores.append(autor)
        session.add(libro)
        session.commit()
    return _a_read(libro)


def desasociar_autor(session: Session, libro_id: int, autor_id: int) -> None:
    libro = obtener_entidad(session, libro_id)
    autor = autor_service.obtener_entidad(session, autor_id)
    if any(existente.id == autor.id for existente in libro.autores):
        libro.autores.remove(autor)
        session.add(libro)
        session.commit()
    else:
        raise Conflicto("El autor no está asociado a ese libro")
