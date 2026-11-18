"""Lógica de negocio de autores."""

from sqlalchemy import delete
from sqlmodel import Session, select

from app.Models import Autor, AutorCreate, AutorRead, AutorUpdate, LibroAutor
from app.errors import NoEncontrado


def _a_read(autor: Autor) -> AutorRead:
    return AutorRead.model_validate(autor)


def listar(session: Session) -> list[AutorRead]:
    autores = session.exec(select(Autor).order_by(Autor.nombre)).all()
    return [_a_read(autor) for autor in autores]


def obtener_entidad(session: Session, autor_id: int) -> Autor:
    autor = session.get(Autor, autor_id)
    if autor is None:
        raise NoEncontrado(f"No existe el autor con id {autor_id}")
    return autor


def obtener(session: Session, autor_id: int) -> AutorRead:
    return _a_read(obtener_entidad(session, autor_id))


def crear(session: Session, datos: AutorCreate) -> AutorRead:
    autor = Autor.model_validate(datos)
    session.add(autor)
    session.commit()
    session.refresh(autor)
    return _a_read(autor)


def actualizar(session: Session, autor_id: int, datos: AutorUpdate) -> AutorRead:
    autor = obtener_entidad(session, autor_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(autor, campo, valor)
    session.add(autor)
    session.commit()
    session.refresh(autor)
    return _a_read(autor)


def eliminar(session: Session, autor_id: int) -> None:
    """Borra el autor y lo desasocia de sus libros (la tabla intermedia cae)."""
    autor = obtener_entidad(session, autor_id)
    session.execute(delete(LibroAutor).where(LibroAutor.autor_id == autor_id))
    session.delete(autor)
    session.commit()
