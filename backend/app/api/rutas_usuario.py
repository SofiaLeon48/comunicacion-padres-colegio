from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import GESTION, PERSONAL, no_encontrado, requiere_modulo, requiere_roles
from app.core.security import hashear_password
from app.core.validacion import campos, obligatorios
from app.models.usuario import Usuario
from app.repositories.rol_repo import RolRepository
from app.repositories.usuario_repo import UsuarioRepository

router = APIRouter(prefix="/usuarios", tags=["Usuarios y Roles - usuarios"],
                   dependencies=[Depends(requiere_modulo("usuarios"))])
repo = UsuarioRepository()
roles = RolRepository()
gestion = Depends(requiere_roles(*GESTION))


def _validar_rol_asignable(rol_id: int, actor: dict) -> None:
    rol = roles.obtener(rol_id)
    if not rol:
        raise HTTPException(status_code=400, detail="El rol indicado no existe o está inactivo.")


@router.get("/", response_model=list[Usuario],
            dependencies=[Depends(requiere_roles(*PERSONAL))])
def listar_usuarios(rol: str | None = None, buscar: str | None = None, incluir_inactivos: bool = False):
    """Filtros opcionales: `rol` (coordinacion, docente, acudiente) y `buscar` (nombre o correo)."""
    return repo.listar_con_rol(rol, buscar, incluir_inactivos)


@router.get("/{usuario_id}", response_model=Usuario,
            dependencies=[Depends(requiere_roles(*PERSONAL))])
def obtener_usuario(usuario_id: int):
    usuario = repo.obtener_con_rol(usuario_id, incluir_inactivos=True)
    if not usuario:
        raise no_encontrado("Usuario")
    return usuario


@router.post("/", response_model=Usuario, status_code=201)
def crear_usuario(datos: Usuario, actor: dict = gestion):
    obligatorios(datos, "nombre", "correo", "password", "rol_id")
    _validar_rol_asignable(datos.rol_id, actor)
    valores = campos(datos, "nombre", "correo", "telefono", "rol_id")
    valores["password_hash"] = hashear_password(datos.password)
    nuevo = repo.crear(valores)
    return repo.obtener_con_rol(nuevo["id"])


@router.patch("/{usuario_id}", response_model=Usuario)
def actualizar_usuario(usuario_id: int, datos: Usuario, actor: dict = gestion):
    actual = repo.obtener_con_rol(usuario_id, incluir_inactivos=True)
    if not actual:
        raise no_encontrado("Usuario")
    valores = campos(datos, "nombre", "correo", "telefono", "rol_id", editar=True)
    if datos.password:
        valores["password_hash"] = hashear_password(datos.password)
    if "rol_id" in valores:
        _validar_rol_asignable(valores["rol_id"], actor)
    repo.actualizar(usuario_id, valores)
    return repo.obtener_con_rol(usuario_id, incluir_inactivos=True)


@router.delete("/{usuario_id}")
def eliminar_usuario(usuario_id: int, actor: dict = gestion):
    if usuario_id == actor["id"]:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propio usuario.")
    objetivo = repo.obtener_con_rol(usuario_id)
    if not objetivo:
        raise no_encontrado("Usuario")
    repo.desactivar(usuario_id)
    return {"mensaje": "Usuario desactivado correctamente (borrado lógico)."}


@router.post("/{usuario_id}/reactivar")
def reactivar_usuario(usuario_id: int, actor: dict = gestion):
    if not repo.reactivar(usuario_id):
        raise no_encontrado("Usuario inactivo")
    return {"mensaje": "Usuario reactivado correctamente."}
