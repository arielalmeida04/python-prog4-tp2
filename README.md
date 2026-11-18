# TP2 — Sistema de Biblioteca (FastAPI + SQLModel)

API REST para administrar el catálogo de una biblioteca, sus socios y los
préstamos. Toda la lógica de negocio vive en la capa `Service`; los
`Controllers` solo traducen HTTP ↔ servicios.

## Requisitos

- Python 3.11 o superior (probado con 3.13).
- SQLite (viene incluido con Python).

## Instalación

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Datos iniciales (opcional)

Crea la base `biblioteca.db` con un bibliotecario y un socio de prueba:

```bash
.venv/bin/python -m app.seed
```

| Usuario | Email | Contraseña | Rol |
|---|---|---|---|
| Bibliotecario | `admin@biblioteca.com` | `admin123` | bibliotecario |
| Socio | `socio@biblioteca.com` | `socio123` | socio |

## Ejecutar la API

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

- Documentación interactiva: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

## Autenticación

Todos los endpoints (salvo `POST /auth/login` y `/`) piden un token Bearer.

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@biblioteca.com","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/libros
```

- **bibliotecario**: administra el catálogo completo (autores, libros, socios,
  préstamos y devoluciones).
- **socio**: solo puede consultar sus propios préstamos
  (`GET /socios/{id}/prestamos`); el resto responde 403.
- Los usuarios se crean con `POST /auth/usuarios` (solo bibliotecario).

## Endpoints

| Método | Ruta | Rol | Éxito | Descripción |
|---|---|---|---|---|
| POST | `/auth/login` | público | 200 | Devuelve el token |
| POST | `/auth/usuarios` | bibliotecario | 201 | Crea un usuario |
| GET | `/autores` | bibliotecario | 200 | Lista autores |
| GET | `/autores/{id}` | bibliotecario | 200 | Obtiene un autor |
| POST | `/autores` | bibliotecario | 201 | Crea un autor |
| PUT | `/autores/{id}` | bibliotecario | 200 | Modifica un autor |
| DELETE | `/autores/{id}` | bibliotecario | 204 | Borra y desasocia de libros |
| GET | `/libros?disponibles=true` | bibliotecario | 200 | Lista libros (filtra stock > 0) |
| GET | `/libros/{id}` | bibliotecario | 200 | Libro con sus autores |
| POST | `/libros` | bibliotecario | 201 | Crea un libro |
| PUT | `/libros/{id}` | bibliotecario | 200 | Modifica un libro |
| DELETE | `/libros/{id}` | bibliotecario | 204 | Borra (409 si tiene préstamos) |
| POST | `/libros/{id}/autores/{autor_id}` | bibliotecario | 200 | Asocia autor (N-N) |
| DELETE | `/libros/{id}/autores/{autor_id}` | bibliotecario | 204 | Desasocia autor |
| GET | `/socios?activos=true` | bibliotecario | 200 | Lista socios |
| GET | `/socios/{id}` | bibliotecario | 200 | Obtiene un socio |
| POST | `/socios` | bibliotecario | 201 | Crea un socio |
| PUT | `/socios/{id}` | bibliotecario | 200 | Modifica un socio |
| DELETE | `/socios/{id}` | bibliotecario | 204 | Borra (409 si tiene préstamos) |
| GET | `/socios/{id}/prestamos?activos=true` | bibliotecario / socio dueño | 200 | Préstamos del socio |
| GET | `/prestamos?activos=&socio_id=` | bibliotecario | 200 | Lista préstamos |
| GET | `/prestamos/{id}` | bibliotecario | 200 | Obtiene un préstamo |
| POST | `/prestamos` | bibliotecario | 201 | Registra un préstamo |
| POST | `/prestamos/{id}/devolucion` | bibliotecario | 200 | Registra la devolución |

## Reglas de negocio

| # | Regla | HTTP |
|---|---|---|
| 1 | Un socio no puede tener más de 3 préstamos activos | 409 |
| 2 | No se presta un libro sin stock; al prestar se descuenta 1 | 409 |
| 3 | Un socio inactivo no puede pedir préstamos | 403 |
| 4 | Plazo de 14 días (`fecha_vencimiento = fecha_prestamo + 14`) | — |
| 5 | Al devolver se repone el stock y la multa es $100 × día de atraso | — |
| 6 | No se puede devolver un préstamo ya devuelto | 409 |
| 7 | Recurso inexistente | 404 |
| 8 | ISBN o email duplicado | 409 |

El descuento de stock usa un `UPDATE ... WHERE stock > 0` condicional y la
operación se confirma en una sola transacción: si algo falla, no queda stock
descontado a medias.

## Estructura

```
app/
├── main.py              # app FastAPI, routers y manejadores de error
├── database.py          # engine SQLite, sesión por request y create_all
├── errors.py            # errores de dominio → 404 / 409 / 403 / 401 / 422
├── security.py          # tokens HMAC, hash PBKDF2 y dependencias de rol
├── seed.py              # datos iniciales para probar a mano
├── Models/              # tablas SQLModel + schemas de entrada/salida
├── Service/             # TODA la lógica de negocio
└── Controllers/         # endpoints HTTP (sin lógica de negocio)
Tests/                   # pytest con base SQLite en memoria
```

## Tests

```bash
.venv/bin/python -m pytest --cov=app --cov-report=term-missing
```

- Base SQLite en memoria (`StaticPool`), recreada en cada test.
- Cada regla de negocio tiene su caso feliz y su caso de error.
- Cobertura actual: **94 %** (39 tests).

## Decisiones de diseño

- **Errores de dominio**: los servicios lanzan `NoEncontrado`, `Conflicto`,
  `Prohibido`, etc. y `main.py` los convierte al código HTTP. Así el service no
  depende de FastAPI y se puede testear aislado.
- **Borrado mixto**: la tabla `libro_autor` se limpia automáticamente; los
  préstamos **no** se borran en cascada, para no perder el historial. Si un
  libro o socio tiene préstamos, el borrado responde 409.
- **Préstamos**: las fechas y la multa se calculan siempre en el service; el
  cliente solo envía `socio_id` y `libro_id`.
