"""Configuración de la base de datos SQLite y de la sesión por request."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, event
from sqlmodel import Session, SQLModel, create_engine

RUTA_BD = Path(__file__).resolve().parent.parent / "biblioteca.db"
URL_BD = f"sqlite:///{RUTA_BD}"


def crear_engine(url: str = URL_BD, **opciones) -> Engine:
    """Crea un engine SQLite con claves foráneas activas.

    Las claves foráneas de SQLite vienen desactivadas por defecto, por eso se
    activa el PRAGMA en cada conexión nueva.
    """
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        **opciones,
    )

    @event.listens_for(engine, "connect")
    def _activar_claves_foraneas(conexion, _registro):  # pragma: no cover - hook
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = crear_engine()


def crear_tablas(engine_destino: Engine | None = None) -> None:
    """Crea todas las tablas registradas en los modelos."""
    import app.Models  # noqa: F401  (registra las tablas en el metadata)

    SQLModel.metadata.create_all(engine_destino or engine)


def get_session() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: una sesión nueva por request."""
    with Session(engine, expire_on_commit=False) as session:
        yield session
