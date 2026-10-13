from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import GESTION, no_encontrado, requiere_modulo, requiere_roles
from app.models.comun import Mensaje
from app.models.configuracion import (ModuloActualizar, ModuloCrear, ModuloSalida, PermisoCambio,
                                      PermisoItem)
from app.repositories.modulo_repo import ModuloRepository
from app.repositories.rol_modulo_repo import RolModuloRepository
from app.repositories.rol_repo import RolRepository
from app.services import actividad

router = APIRouter(prefix="/configuracion", tags=["Configuración - módulos y permisos"],
                   dependencies=[Depends(requiere_modulo("configuracion"))])
modulos = ModuloRepository()
permisos = RolModuloRepository()
roles = RolRepository()
gestion = Depends(requiere_roles(*GESTION))


@router.get("/modulos", response_model=list[ModuloSalida])
def listar_modulos(incluir_inactivos: bool = False, _: dict = gestion):
    return modulos.listar(incluir_inactivos)


@router.post("/modulos", response_model=ModuloSalida, status_code=201)
def crear_modulo(datos: ModuloCrear, actor: dict = gestion):
    m = modulos.crear(datos.model_dump())
    actividad.registrar(actor, "crear", "modulos", m["id"], m["nombre"])
    return m


@router.patch("/modulos/{modulo_id}", response_model=ModuloSalida)
def actualizar_modulo(modulo_id: int, datos: ModuloActualizar, actor: dict = gestion):
    actual = modulos.obtener(modulo_id, incluir_inactivos=True)
    if not actual:
        raise no_encontrado("Módulo")
    if actual["clave"] == "configuracion" and datos.estado == "inactivo":
        raise HTTPException(status_code=400, detail="El módulo Configuración no se puede desactivar.")
    m = modulos.actualizar(modulo_id, datos.model_dump(exclude_unset=True))
    actividad.registrar(actor, "actualizar", "modulos", modulo_id)
    return m


@router.get("/permisos", response_model=list[PermisoItem], summary="Matriz rol x módulo")
def matriz_permisos(_: dict = gestion):
    return permisos.matriz()


@router.put("/permisos", response_model=Mensaje, summary="Dar o quitar un módulo a un rol")
def cambiar_permiso(datos: PermisoCambio, actor: dict = gestion):
    rol = roles.obtener(datos.rol_id)
    modulo = modulos.obtener(datos.modulo_id)
    if not rol or not modulo:
        raise HTTPException(status_code=400, detail="Rol o módulo inválido.")
    if rol["nombre"] == "coordinacion" and modulo["clave"] == "configuracion" and not datos.permitido:
        raise HTTPException(status_code=400,
                            detail="Coordinación no puede perder el acceso a Configuración (quedaría bloqueada).")
    permisos.asignar(datos.rol_id, datos.modulo_id, datos.permitido)
    accion = "asignar_modulo" if datos.permitido else "quitar_modulo"
    actividad.registrar(actor, accion, "rol_modulo", None, f"{rol['nombre']} → {modulo['clave']}")
    return {"mensaje": f"Permiso actualizado: {modulo['nombre']} {'asignado a' if datos.permitido else 'retirado de'} {rol['nombre']}."}
