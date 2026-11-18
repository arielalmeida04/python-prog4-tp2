"""Carga datos iniciales para probar la API a mano.

Uso:
    .venv/bin/python -m app.seed

Crea (si no existen):
    bibliotecario: admin@biblioteca.com / admin123
    socio:         socio@biblioteca.com / socio123 (ligado a un socio demo)
"""

from sqlmodel import Session, select

from app.database import crear_tablas, engine
from app.Models import Socio, Usuario
from app.security import hashear_password

ADMIN_EMAIL = "admin@biblioteca.com"
ADMIN_PASSWORD = "admin123"
SOCIO_EMAIL = "socio@biblioteca.com"
SOCIO_PASSWORD = "socio123"


def main() -> None:
    crear_tablas()
    with Session(engine, expire_on_commit=False) as session:
        if not session.exec(select(Usuario).where(Usuario.email == ADMIN_EMAIL)).first():
            session.add(
                Usuario(
                    email=ADMIN_EMAIL,
                    password_hash=hashear_password(ADMIN_PASSWORD),
                    rol="bibliotecario",
                )
            )
            print(f"Bibliotecario creado: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

        socio = session.exec(select(Socio).where(Socio.email == SOCIO_EMAIL)).first()
        if socio is None:
            socio = Socio(nombre="Socio Demo", email=SOCIO_EMAIL, activo=True)
            session.add(socio)
            session.commit()
            session.refresh(socio)

        if not session.exec(select(Usuario).where(Usuario.email == SOCIO_EMAIL)).first():
            session.add(
                Usuario(
                    email=SOCIO_EMAIL,
                    password_hash=hashear_password(SOCIO_PASSWORD),
                    rol="socio",
                    socio_id=socio.id,
                )
            )
            print(f"Socio creado: {SOCIO_EMAIL} / {SOCIO_PASSWORD}")

        session.commit()
    print("Datos iniciales listos.")


if __name__ == "__main__":  # pragma: no cover
    main()
