"""Usuario para autenticación (rol bibliotecario o socio)."""

from sqlmodel import Field, SQLModel

ROLES_VALIDOS = ("bibliotecario", "socio")


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(min_length=3, max_length=120, unique=True, index=True)
    password_hash: str
    rol: str = Field(default="socio", max_length=20)
    socio_id: int | None = Field(
        default=None, foreign_key="socio.id", ondelete="SET NULL"
    )


class UsuarioCreate(SQLModel):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=6, max_length=72)
    rol: str = Field(default="socio")
    socio_id: int | None = None


class UsuarioRead(SQLModel):
    id: int
    email: str
    rol: str
    socio_id: int | None


class LoginRequest(SQLModel):
    email: str
    password: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
