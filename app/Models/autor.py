"""Modelos de Autor y sus schemas de entrada/salida."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.Models.libro_autor import LibroAutor

if TYPE_CHECKING:  # solo para los type checkers, evita la importación circular
    from app.Models.libro import Libro


class AutorBase(SQLModel):
    nombre: str = Field(min_length=1, max_length=120)
    nacionalidad: str = Field(min_length=1, max_length=80)


class Autor(AutorBase, table=True):
    __tablename__ = "autor"

    id: int | None = Field(default=None, primary_key=True)
    libros: list["Libro"] = Relationship(
        back_populates="autores", link_model=LibroAutor
    )


class AutorCreate(AutorBase):
    pass


class AutorUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    nacionalidad: str | None = Field(default=None, min_length=1, max_length=80)


class AutorRead(AutorBase):
    id: int
