"""Modelos de Socio y sus schemas de entrada/salida."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:  # solo para los type checkers, evita la importación circular
    from app.Models.prestamo import Prestamo


class SocioBase(SQLModel):
    nombre: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=120, unique=True, index=True)
    activo: bool = True


class Socio(SocioBase, table=True):
    __tablename__ = "socio"

    id: int | None = Field(default=None, primary_key=True)
    prestamos: list["Prestamo"] = Relationship(back_populates="socio")


class SocioCreate(SocioBase):
    pass


class SocioUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, min_length=3, max_length=120)
    activo: bool | None = None


class SocioRead(SocioBase):
    id: int
