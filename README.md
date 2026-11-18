# TP2 — Sistema de Biblioteca

API REST para gestionar libros, autores, socios y préstamos.
FastAPI + SQLModel + SQLite.

## Requisitos

- Python 3.11 o superior

## Instalación

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Ejecutar

```bash
.venv/bin/python -m app.seed    # opcional: carga usuarios y un socio de prueba
.venv/bin/python -m uvicorn app.main:app --reload
```

Documentación interactiva: <http://127.0.0.1:8000/docs>

Usuarios de prueba:

| Email | Contraseña | Rol |
|---|---|---|
| `admin@biblioteca.com` | `admin123` | bibliotecario |
| `socio@biblioteca.com` | `socio123` | socio |

## Tests

```bash
.venv/bin/python -m pytest --cov=app
```

39 tests con SQLite en memoria y 94 % de cobertura.

## Estructura

```
.
├── app/
│   ├── Models/        # tablas y schemas
│   ├── Service/       # lógica de negocio
│   ├── Controllers/   # endpoints HTTP
│   ├── database.py    # conexión a SQLite
│   ├── security.py    # login y roles
│   └── main.py        # aplicación FastAPI
└── Tests/             # tests con pytest
```

## Endpoints

| Método | Ruta |
|---|---|
| POST | `/auth/login` |
| GET / POST | `/autores` |
| GET / PUT / DELETE | `/autores/{id}` |
| GET / POST | `/libros` |
| GET / PUT / DELETE | `/libros/{id}` |
| GET | `/libros?disponibles=true` |
| POST | `/libros/{id}/autores/{autor_id}` |
| GET / POST | `/socios` |
| GET / PUT / DELETE | `/socios/{id}` |
| GET | `/socios/{id}/prestamos?activos=true` |
| GET / POST | `/prestamos` |
| GET | `/prestamos/{id}` |
| POST | `/prestamos/{id}/devolucion` |

Todos los endpoints, salvo `/auth/login`, piden `Authorization: Bearer <token>`.
