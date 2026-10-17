from fastapi import APIRouter, Depends

from app.core.deps import GESTION, UsuarioActual, no_encontrado, requiere_modulo, requiere_roles
from app.core.validacion import campos, obligatorios
from app.models.rol import Rol
from app.repositories.rol_repo import RolRepository

router = APIRouter(prefix="/roles", tags=["Configuración - roles"],
                   dependencies=[Depends(requiere_modulo("configuracion"))])
repo = RolRepository()
solo_admin = Depends(requiere_roles(*GESTION))


@router.get("/", response_model=list[Rol])
def listar_roles(_: UsuarioActual, incluir_inactivos: bool = False):
    return repo.listar(incluir_inactivos)


@router.get("/{rol_id}", response_model=Rol)
def obtener_rol(rol_id: int, _: UsuarioActual):
    rol = repo.obtener(rol_id)
    if not rol:
        raise no_encontrado("Rol")
    return rol


@router.post("/", response_model=Rol, status_code=201)
def crear_rol(datos: Rol, usuario: dict = solo_admin):
    obligatorios(datos, "nombre")
    rol = repo.crear(campos(datos, "nombre", "descripcion"))
    return rol


@router.patch("/{rol_id}", response_model=Rol)
def actualizar_rol(rol_id: int, datos: Rol, usuario: dict = solo_admin):
    rol = repo.actualizar(rol_id, campos(datos, "nombre", "descripcion", editar=True))
    if not rol:
        raise no_encontrado("Rol")
    return rol


@router.delete("/{rol_id}")
def eliminar_rol(rol_id: int, usuario: dict = solo_admin):
    if not repo.desactivar(rol_id):
        raise no_encontrado("Rol")
    return {"mensaje": "Rol desactivado correctamente."}
