from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import UsuarioActual
from app.core.security import crear_token, hashear_password, verificar_password
from app.models.auth import Token
from app.models.comun import Mensaje
from app.models.usuario import CambioPassword, PerfilActualizar, UsuarioSalida
from app.repositories.usuario_repo import UsuarioRepository
from app.services import actividad

router = APIRouter(prefix="/auth", tags=["Autenticación"])
repo = UsuarioRepository()


@router.post("/login", response_model=Token, summary="Iniciar sesión (correo + contraseña)")
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """En el formulario, **username** es el correo del usuario."""
    usuario = repo.obtener_por_correo(form.username)
    if not usuario or not verificar_password(form.password, usuario["password_hash"]):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    if usuario["estado"] != "activo":
        raise HTTPException(status_code=403, detail="Tu usuario está inactivo. Contacta a coordinación.")
    repo.registrar_acceso(usuario["id"])
    actividad.registrar(usuario, "login", "usuarios", usuario["id"])
    return {"access_token": crear_token(usuario["id"], usuario["rol"]), "usuario": usuario}


@router.get("/me", response_model=UsuarioSalida, summary="Mi perfil")
def mi_perfil(usuario: UsuarioActual):
    return usuario


@router.patch("/me", response_model=UsuarioSalida, summary="Actualizar mi perfil")
def actualizar_perfil(datos: PerfilActualizar, usuario: UsuarioActual):
    repo.actualizar(usuario["id"], datos.model_dump(exclude_unset=True))
    return repo.obtener_con_rol(usuario["id"])


@router.put("/me/password", response_model=Mensaje, summary="Cambiar mi contraseña")
def cambiar_password(datos: CambioPassword, usuario: UsuarioActual):
    if not verificar_password(datos.password_actual, usuario["password_hash"]):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta.")
    repo.actualizar(usuario["id"], {"password_hash": hashear_password(datos.password_nueva)})
    actividad.registrar(usuario, "cambiar_password", "usuarios", usuario["id"])
    return {"mensaje": "Contraseña actualizada correctamente."}
