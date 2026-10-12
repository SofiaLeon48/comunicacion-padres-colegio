"""
Seguridad: cifrado de contraseñas (bcrypt) y tokens de sesión (JWT).
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


def hashear_password(password: str) -> str:
    """Devuelve el hash bcrypt de la contraseña (incluye un 'salt' aleatorio)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def crear_token(usuario_id: int, rol: str) -> str:
    """Genera un JWT firmado con el id y el rol del usuario."""
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "rol": rol,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.JWT_EXPIRA_MINUTOS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITMO)


def decodificar_token(token: str) -> dict | None:
    """Devuelve el contenido del token, o None si es inválido o expiró."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITMO])
    except jwt.PyJWTError:
        return None
