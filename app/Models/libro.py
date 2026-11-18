"""Modelos de Libro y sus schemas de entrada/salida."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.Models.autor import AutorRead
from app.Models.libro_autor import LibroAutor

if TYPE_CHECKING:  # solo para los type checkers, evita la importación circular
    from app.Models.autor import Autor


class LibroBase(SQLModel):
    titulo: str = Field(min_length=1, max_length=200)
    isbn: str = Field(min_length=1, max_length=40, unique=True, index=True)
    stock: int = Field(default=0, ge=0)
    anio: int = Field(ge=0, le=2100)


class Libro(LibroBase, table=True):
    __tablename__ = "libro"

    id: int | None = Field(default=None, primary_key=True)
    autores: list["Autor"] = Relationship(
        back_populates="libros", link_model=LibroAutor
    )


class LibroCreate(LibroBase):
    pass


class LibroUpdate(SQLModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    isbn: str | None = Field(default=None, min_length=1, max_length=40)
    stock: int | None = Field(default=None, ge=0)
    anio: int | None = Field(default=None, ge=0, le=2100)


class LibroRead(LibroBase):
    id: int
    autores: list[AutorRead] = Field(default_factory=list)
