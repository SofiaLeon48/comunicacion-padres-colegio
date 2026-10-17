from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import GESTION, no_encontrado, requiere_modulo, requiere_roles
from app.models.modelos import Modelos
from app.repositories.modulo_repo import ModuloRepository
from app.repositories.rol_modulo_repo import RolModuloRepository
from app.repositories.rol_repo import RolRepository

router = APIRouter(prefix="/configuracion", tags=["Configuración - módulos y permisos"],
                   dependencies=[Depends(requiere_modulo("configuracion"))])
modulos = ModuloRepository()
permisos = RolModuloRepository()
roles = RolRepository()
gestion = Depends(requiere_roles(*GESTION))


@router.get("/modulos", response_model=list[Modelos.ModuloSalida])
def listar_modulos(incluir_inactivos: bool = False, _: dict = gestion):
    return modulos.listar(incluir_inactivos)


@router.post("/modulos", response_model=Modelos.ModuloSalida, status_code=201)
def crear_modulo(datos: Modelos.ModuloCrear, _: dict = gestion):
    return modulos.crear(datos.model_dump())


@router.patch("/modulos/{modulo_id}", response_model=Modelos.ModuloSalida)
def actualizar_modulo(modulo_id: int, datos: Modelos.ModuloActualizar, actor: dict = gestion):
    actual = modulos.obtener(modulo_id, incluir_inactivos=True)
    if not actual:
        raise no_encontrado("Módulo")
    return modulos.actualizar(modulo_id, datos.model_dump(exclude_unset=True))


@router.delete("/modulos/{modulo_id}", response_model=Modelos.Mensaje, summary="Desactivar un módulo (sale del menú)")
def desactivar_modulo(modulo_id: int, _: dict = gestion):
    actual = modulos.obtener(modulo_id)
    if not actual:
        raise no_encontrado("Módulo")
    if actual["clave"] == "configuracion":
        raise HTTPException(status_code=400, detail="El módulo Configuración no se puede desactivar.")
    modulos.desactivar(modulo_id)
    return {"mensaje": f"Módulo {actual['nombre']} desactivado."}


@router.post("/modulos/{modulo_id}/reactivar", response_model=Modelos.Mensaje, summary="Reactivar un módulo")
def reactivar_modulo(modulo_id: int, _: dict = gestion):
    actual = modulos.obtener(modulo_id, incluir_inactivos=True)
    if not actual:
        raise no_encontrado("Módulo")
    modulos.reactivar(modulo_id)
    return {"mensaje": f"Módulo {actual['nombre']} reactivado."}


@router.get("/permisos", response_model=list[Modelos.PermisoItem], summary="Matriz rol x módulo")
def matriz_permisos(_: dict = gestion):
    return permisos.matriz()


@router.put("/permisos", response_model=Modelos.Mensaje, summary="Dar o quitar un módulo a un rol")
def cambiar_permiso(datos: Modelos.PermisoCambio, actor: dict = gestion):
    rol = roles.obtener(datos.rol_id)
    modulo = modulos.obtener(datos.modulo_id)
    if not rol or not modulo:
        raise HTTPException(status_code=400, detail="Rol o módulo inválido.")
    if rol["nombre"] == "coordinacion" and modulo["clave"] == "configuracion" and not datos.permitido:
        raise HTTPException(status_code=400,
                            detail="Coordinación no puede perder el acceso a Configuración (quedaría bloqueada).")
    permisos.asignar(datos.rol_id, datos.modulo_id, datos.permitido)
    return {"mensaje": f"Permiso actualizado: {modulo['nombre']} {'asignado a' if datos.permitido else 'retirado de'} {rol['nombre']}."}
