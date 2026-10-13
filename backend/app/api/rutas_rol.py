from fastapi import APIRouter, Depends

from app.core.deps import GESTION, UsuarioActual, no_encontrado, requiere_modulo, requiere_roles
from app.models.comun import Mensaje
from app.models.rol import RolActualizar, RolCrear, RolSalida
from app.repositories.rol_repo import RolRepository
from app.services import actividad

router = APIRouter(prefix="/roles", tags=["Configuración - roles"],
                   dependencies=[Depends(requiere_modulo("configuracion"))])
repo = RolRepository()
solo_admin = Depends(requiere_roles(*GESTION))


@router.get("/", response_model=list[RolSalida])
def listar_roles(_: UsuarioActual, incluir_inactivos: bool = False):
    return repo.listar(incluir_inactivos)


@router.get("/{rol_id}", response_model=RolSalida)
def obtener_rol(rol_id: int, _: UsuarioActual):
    rol = repo.obtener(rol_id)
    if not rol:
        raise no_encontrado("Rol")
    return rol


@router.post("/", response_model=RolSalida, status_code=201)
def crear_rol(datos: RolCrear, usuario: dict = solo_admin):
    rol = repo.crear(datos.model_dump())
    actividad.registrar(usuario, "crear", "roles", rol["id"], rol["nombre"])
    return rol


@router.patch("/{rol_id}", response_model=RolSalida)
def actualizar_rol(rol_id: int, datos: RolActualizar, usuario: dict = solo_admin):
    rol = repo.actualizar(rol_id, datos.model_dump(exclude_unset=True))
    if not rol:
        raise no_encontrado("Rol")
    actividad.registrar(usuario, "actualizar", "roles", rol_id)
    return rol


@router.delete("/{rol_id}", response_model=Mensaje)
def eliminar_rol(rol_id: int, usuario: dict = solo_admin):
    if not repo.desactivar(rol_id):
        raise no_encontrado("Rol")
    actividad.registrar(usuario, "eliminar", "roles", rol_id)
    return {"mensaje": "Rol desactivado correctamente."}
