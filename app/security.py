"""Autenticación simple con tokens firmados (HMAC-SHA256) y contraseñas PBKDF2.

No se usan librerías externas: alcanza para el TP y evita dependencias extra.
"""

import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.database import get_session
from app.errors import NoAutorizado, Prohibido
from app.Models import Usuario

CLAVE_SECRETA = os.getenv("BIBLIOTECA_SECRET", "clave-de-desarrollo-cambiar")
HORAS_VALIDEZ = 8
ITERACIONES_PBKDF2 = 120_000

esquema_bearer = HTTPBearer(auto_error=False)


def hashear_password(password: str) -> str:
    """Devuelve "sal$hash" usando PBKDF2-HMAC-SHA256."""
    sal = os.urandom(16)
    derivada = hashlib.pbkdf2_hmac("sha256", password.encode(), sal, ITERACIONES_PBKDF2)
    return f"{sal.hex()}${derivada.hex()}"


def verificar_password(password: str, almacenada: str) -> bool:
    try:
        sal_hex, hash_hex = almacenada.split("$", 1)
        sal = bytes.fromhex(sal_hex)
    except ValueError:
        return False
    derivada = hashlib.pbkdf2_hmac("sha256", password.encode(), sal, ITERACIONES_PBKDF2)
    return hmac.compare_digest(derivada.hex(), hash_hex)


def _firmar(contenido: str) -> str:
    return hmac.new(CLAVE_SECRETA.encode(), contenido.encode(), hashlib.sha256).hexdigest()


def crear_token(usuario_id: int) -> str:
    payload = {"sub": usuario_id, "exp": int(time.time()) + HORAS_VALIDEZ * 3600}
    cuerpo = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{cuerpo}.{_firmar(cuerpo)}"


def leer_token(token: str) -> dict:
    cuerpo, _, firma = token.partition(".")
    if not cuerpo or not firma or not hmac.compare_digest(_firmar(cuerpo), firma):
        raise NoAutorizado("Token inválido")
    try:
        relleno = "=" * (-len(cuerpo) % 4)
        datos = json.loads(base64.urlsafe_b64decode(cuerpo + relleno))
    except (ValueError, json.JSONDecodeError):
        raise NoAutorizado("Token inválido") from None
    if datos.get("exp", 0) < time.time():
        raise NoAutorizado("El token expiró")
    return datos


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    session: Session = Depends(get_session),
) -> Usuario:
    """Dependencia: resuelve el usuario a partir del token Bearer."""
    if credenciales is None:
        raise NoAutorizado("Falta el token de autenticación")
    datos = leer_token(credenciales.credentials)
    usuario = session.get(Usuario, datos["sub"])
    if usuario is None:
        raise NoAutorizado("Usuario inexistente")
    return usuario


def requiere_bibliotecario(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    """Dependencia: solo permite el rol bibliotecario."""
    if usuario.rol != "bibliotecario":
        raise Prohibido("Solo el bibliotecario puede realizar esta acción")
    return usuario
