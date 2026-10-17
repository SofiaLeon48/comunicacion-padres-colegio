from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from app.core.deps import UsuarioActual
from app.core.security import crear_token, hashear_password, verificar_password
from app.core.validacion import campos
from app.models.modulo import Modulo
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.repositories.rol_modulo_repo import RolModuloRepository
from app.repositories.rol_repo import RolRepository
from app.repositories.usuario_repo import UsuarioRepository

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
    return {"access_token": crear_token(usuario["id"], usuario["rol"]), "token_type": "bearer",
            "usuario": Usuario.model_validate(usuario).model_dump(mode="json"),   # sin password_hash
            "modulos": permisos.modulos_de_rol(usuario["rol_id"])}


@router.get("/roles", response_model=list[Rol], summary="Roles disponibles (para el login)")
def roles_login():
    """Público: alimenta el selector de rol de la pantalla de inicio de sesión."""
    return roles.listar()


@router.post("/login", summary="Iniciar sesión con correo, contraseña y rol")
def login(correo: EmailStr = Body(examples=["coordinacion@colegio.edu.co"]),
          password: str = Body(examples=["Colegio2026*"]),
          rol: str = Body(examples=["coordinacion"], description="Debe coincidir con el rol del usuario")):
    """Usado por el frontend. Valida que el rol elegido sea el del usuario y devuelve
    el token y los **módulos permitidos** (tabla rol_modulo) para construir el menú."""
    return _autenticar(correo, password, rol)


@router.post("/token", include_in_schema=False)
def token_swagger(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login de formulario para el botón Authorize de Swagger (username = correo)."""
    return _autenticar(form.username, form.password, None)


@router.get("/me", response_model=Usuario, summary="Mi perfil")
def mi_perfil(usuario: UsuarioActual):
    return usuario


@router.get("/mis-modulos", response_model=list[Modulo], summary="Módulos del menú según mi rol")
def mis_modulos(usuario: UsuarioActual):
    return permisos.modulos_de_rol(usuario["rol_id"])


@router.patch("/me", response_model=Usuario, summary="Actualizar mi perfil (nombre y teléfono)")
def actualizar_perfil(datos: Usuario, usuario: UsuarioActual):
    repo.actualizar(usuario["id"], campos(datos, "nombre", "telefono", editar=True))
    return repo.obtener_con_rol(usuario["id"])


@router.put("/me/password", summary="Cambiar mi contraseña")
def cambiar_password(usuario: UsuarioActual, password_actual: str = Body(),
                     password_nueva: str = Body(min_length=8, max_length=72)):
    if not verificar_password(password_actual, usuario["password_hash"]):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta.")
    repo.actualizar(usuario["id"], {"password_hash": hashear_password(password_nueva)})
    return {"mensaje": "Contraseña actualizada correctamente."}
