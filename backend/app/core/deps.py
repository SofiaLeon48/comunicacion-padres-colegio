"""
Dependencias de FastAPI para autenticación y autorización.

    @router.get("/")
    def listar(usuario: UsuarioActual): ...                       # cualquier usuario logueado

    @router.post("/", dependencies=[Depends(requiere_roles(*GESTION))])
    def crear(...): ...                                             # solo admin y coordinación
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decodificar_token
from app.repositories.usuario_repo import UsuarioRepository

# Grupos de roles reutilizables
GESTION = ("admin", "coordinacion")                 # administran la plataforma
PERSONAL = ("admin", "coordinacion", "docente")     # personal del colegio

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
_usuarios = UsuarioRepository()


def obtener_usuario_desde_token(token: str) -> dict | None:
    payload = decodificar_token(token)
    if not payload or "sub" not in payload:
        return None
    return _usuarios.obtener_con_rol(int(payload["sub"]))


def usuario_actual(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    usuario = obtener_usuario_desde_token(token)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada. Inicia sesión de nuevo.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


UsuarioActual = Annotated[dict, Depends(usuario_actual)]


def requiere_roles(*roles: str):
    def verificar(usuario: UsuarioActual) -> dict:
        if usuario["rol"] not in roles:
            raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta acción.")
        return usuario
    return verificar


def es_gestion(usuario: dict) -> bool:
    return usuario["rol"] in GESTION


def es_personal(usuario: dict) -> bool:
    return usuario["rol"] in PERSONAL


def no_encontrado(entidad: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{entidad} no encontrado(a).")


def prohibido(detalle: str = "No tienes permiso para realizar esta acción.") -> HTTPException:
    return HTTPException(status_code=403, detail=detalle)
