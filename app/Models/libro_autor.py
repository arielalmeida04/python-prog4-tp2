"""Tabla intermedia de la relación N-N entre Libro y Autor."""

from sqlmodel import Field, SQLModel


class LibroAutor(SQLModel, table=True):
    __tablename__ = "libro_autor"

    libro_id: int = Field(
        foreign_key="libro.id", primary_key=True, ondelete="CASCADE"
    )
    autor_id: int = Field(
        foreign_key="autor.id", primary_key=True, ondelete="CASCADE"
    )
