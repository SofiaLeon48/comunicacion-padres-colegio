from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import GESTION, no_encontrado, requiere_modulo, requiere_roles
from app.core.validacion import campos, obligatorios
from app.models.modulo import Modulo
from app.models.rol_modulo import RolModulo
from app.repositories.modulo_repo import ModuloRepository
from app.repositories.rol_modulo_repo import RolModuloRepository
from app.repositories.rol_repo import RolRepository

router = APIRouter(prefix="/configuracion", tags=["Configuración - módulos y permisos"],
                   dependencies=[Depends(requiere_modulo("configuracion"))])
modulos = ModuloRepository()
permisos = RolModuloRepository()
roles = RolRepository()
gestion = Depends(requiere_roles(*GESTION))


@router.get("/modulos", response_model=list[Modulo])
def listar_modulos(incluir_inactivos: bool = False, _: dict = gestion):
    return modulos.listar(incluir_inactivos)


@router.post("/modulos", response_model=Modulo, status_code=201)
def crear_modulo(datos: Modulo, _: dict = gestion):
    obligatorios(datos, "clave", "nombre", "ruta")
    return modulos.crear(campos(datos, "clave", "nombre", "descripcion", "ruta", "icono", "orden"))


@router.patch("/modulos/{modulo_id}", response_model=Modulo)
def actualizar_modulo(modulo_id: int, datos: Modulo, actor: dict = gestion):
    actual = modulos.obtener(modulo_id, incluir_inactivos=True)
    if not actual:
        raise no_encontrado("Módulo")
    return modulos.actualizar(modulo_id, campos(datos, "nombre", "descripcion", "ruta", "icono", "orden", editar=True))


@router.delete("/modulos/{modulo_id}", summary="Desactivar un módulo (sale del menú)")
def desactivar_modulo(modulo_id: int, _: dict = gestion):
    actual = modulos.obtener(modulo_id)
    if not actual:
        raise no_encontrado("Módulo")
    if actual["clave"] == "configuracion":
        raise HTTPException(status_code=400, detail="El módulo Configuración no se puede desactivar.")
    modulos.desactivar(modulo_id)
    return {"mensaje": f"Módulo {actual['nombre']} desactivado."}


@router.post("/modulos/{modulo_id}/reactivar", summary="Reactivar un módulo")
def reactivar_modulo(modulo_id: int, _: dict = gestion):
    actual = modulos.obtener(modulo_id, incluir_inactivos=True)
    if not actual:
        raise no_encontrado("Módulo")
    modulos.reactivar(modulo_id)
    return {"mensaje": f"Módulo {actual['nombre']} reactivado."}


@router.get("/permisos", response_model=list[RolModulo], summary="Matriz rol x módulo")
def matriz_permisos(_: dict = gestion):
    return permisos.matriz()


@router.put("/permisos", summary="Dar o quitar un módulo a un rol")
def cambiar_permiso(datos: RolModulo, actor: dict = gestion):
    obligatorios(datos, "rol_id", "modulo_id", "permitido")
    rol = roles.obtener(datos.rol_id)
    modulo = modulos.obtener(datos.modulo_id)
    if not rol or not modulo:
        raise HTTPException(status_code=400, detail="Rol o módulo inválido.")
    if rol["nombre"] == "coordinacion" and modulo["clave"] == "configuracion" and not datos.permitido:
        raise HTTPException(status_code=400,
                            detail="Coordinación no puede perder el acceso a Configuración (quedaría bloqueada).")
    permisos.asignar(datos.rol_id, datos.modulo_id, datos.permitido)
    return {"mensaje": f"Permiso actualizado: {modulo['nombre']} {'asignado a' if datos.permitido else 'retirado de'} {rol['nombre']}."}
