"""Modelos de Préstamo y sus schemas de entrada/salida."""

from datetime import date
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:  # solo para los type checkers, evita la importación circular
    from app.Models.libro import Libro
    from app.Models.socio import Socio


class PrestamoBase(SQLModel):
    socio_id: int = Field(foreign_key="socio.id")
    libro_id: int = Field(foreign_key="libro.id")


class Prestamo(PrestamoBase, table=True):
    __tablename__ = "prestamo"

    id: int | None = Field(default=None, primary_key=True)
    fecha_prestamo: date
    fecha_vencimiento: date
    fecha_devolucion: date | None = Field(default=None)
    multa: float = Field(default=0.0, ge=0)

    socio: "Socio" = Relationship(back_populates="prestamos")
    libro: "Libro" = Relationship()


class PrestamoCreate(PrestamoBase):
    """El cliente solo elige socio y libro: las fechas las calcula el service."""


class PrestamoRead(SQLModel):
    id: int
    socio_id: int
    libro_id: int
    fecha_prestamo: date
    fecha_vencimiento: date
    fecha_devolucion: date | None
    multa: float
    socio_nombre: str | None = None
    libro_titulo: str | None = None

    @property
    def activo(self) -> bool:
        return self.fecha_devolucion is None
