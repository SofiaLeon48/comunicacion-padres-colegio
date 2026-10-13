from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import UsuarioActual
from app.core.security import crear_token, hashear_password, verificar_password
from app.models.auth import LoginEntrada, ModuloMenu, RolPublico, Token
from app.models.comun import Mensaje
from app.models.usuario import CambioPassword, PerfilActualizar, UsuarioSalida
from app.repositories.rol_modulo_repo import RolModuloRepository
from app.repositories.rol_repo import RolRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services import actividad

router = APIRouter(prefix="/auth", tags=["Autenticación"])
repo = UsuarioRepository()
roles = RolRepository()
permisos = RolModuloRepository()


def _autenticar(correo: str, password: str, rol: str | None) -> dict:
    usuario = repo.obtener_por_correo(correo)
    if not usuario or not verificar_password(password, usuario["password_hash"]):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    if usuario["estado"] != "activo":
        raise HTTPException(status_code=403, detail="Tu usuario está inactivo. Contacta a coordinación.")
    if rol is not None and usuario["rol"] != rol:
        raise HTTPException(status_code=403, detail="El rol seleccionado no corresponde a este usuario.")
    repo.registrar_acceso(usuario["id"])
    actividad.registrar(usuario, "login", "usuarios", usuario["id"])
    return {"access_token": crear_token(usuario["id"], usuario["rol"]), "usuario": usuario,
            "modulos": permisos.modulos_de_rol(usuario["rol_id"])}


@router.get("/roles", response_model=list[RolPublico], summary="Roles disponibles (para el login)")
def roles_login():
    """Público: alimenta el selector de rol de la pantalla de inicio de sesión."""
    return roles.listar()


@router.post("/login", response_model=Token, summary="Iniciar sesión con correo, contraseña y rol")
def login(datos: LoginEntrada):
    """Usado por el frontend. Valida que el rol elegido sea el del usuario y devuelve
    el token y los **módulos permitidos** (tabla rol_modulo) para construir el menú."""
    return _autenticar(datos.correo, datos.password, datos.rol)


@router.post("/token", response_model=Token, include_in_schema=False)
def token_swagger(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login de formulario para el botón Authorize de Swagger (username = correo)."""
    return _autenticar(form.username, form.password, None)


@router.get("/me", response_model=UsuarioSalida, summary="Mi perfil")
def mi_perfil(usuario: UsuarioActual):
    return usuario


@router.get("/mis-modulos", response_model=list[ModuloMenu], summary="Módulos del menú según mi rol")
def mis_modulos(usuario: UsuarioActual):
    return permisos.modulos_de_rol(usuario["rol_id"])


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
