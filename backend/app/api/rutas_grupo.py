from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import GESTION, UsuarioActual, no_encontrado, prohibido, requiere_roles, requiere_modulo
from app.models.modelos import Modelos
from app.repositories.grupo_repo import GrupoRepository
from app.repositories.estudiante_repo import EstudianteRepository
from app.repositories.usuario_repo import UsuarioRepository

router = APIRouter(prefix="/grupos", tags=["Administración - grupos"],
                   dependencies=[Depends(requiere_modulo("grupos"))])
repo = GrupoRepository()
estudiantes = EstudianteRepository()
usuarios = UsuarioRepository()
gestion = Depends(requiere_roles(*GESTION))


def _validar_director(director_id: int | None) -> None:
    if director_id is None:
        return
    u = usuarios.obtener_con_rol(director_id)
    if not u or u["rol"] not in ("docente", "coordinacion"):
        raise HTTPException(status_code=400, detail="El director de grupo debe ser un docente activo.")


@router.get("/", response_model=list[Modelos.GrupoSalida])
def listar_grupos(usuario: UsuarioActual, anio_lectivo: int | None = None, incluir_inactivos: bool = False):
    """Un acudiente solo ve los grupos donde tiene hijos matriculados."""
    acudiente_id = usuario["id"] if usuario["rol"] == "acudiente" else None
    return repo.listar_detallado(acudiente_id, anio_lectivo, incluir_inactivos)


@router.get("/{grupo_id}", response_model=Modelos.GrupoSalida)
def obtener_grupo(grupo_id: int, usuario: UsuarioActual):
    acudiente_id = usuario["id"] if usuario["rol"] == "acudiente" else None
    grupo = next((c for c in repo.listar_detallado(acudiente_id) if c["id"] == grupo_id), None)
    if not grupo:
        raise no_encontrado("Grupo")
    return grupo


@router.get("/{grupo_id}/estudiantes", response_model=list[Modelos.EstudianteSalida])
def estudiantes_del_grupo(grupo_id: int, usuario: UsuarioActual):
    if usuario["rol"] == "acudiente":
        raise prohibido()
    return estudiantes.listar_detallado(grupo_id=grupo_id)


@router.post("/", response_model=Modelos.GrupoSalida, status_code=201)
def crear_grupo(datos: Modelos.GrupoCrear, actor: dict = gestion):
    _validar_director(datos.director_id)
    grupo = repo.crear(datos.model_dump(exclude_none=True))
    return grupo


@router.patch("/{grupo_id}", response_model=Modelos.GrupoSalida)
def actualizar_grupo(grupo_id: int, datos: Modelos.GrupoActualizar, actor: dict = gestion):
    valores = datos.model_dump(exclude_unset=True)
    _validar_director(valores.get("director_id"))
    grupo = repo.actualizar(grupo_id, valores)
    if not grupo:
        raise no_encontrado("Grupo")
    return grupo


@router.delete("/{grupo_id}", response_model=Modelos.Mensaje)
def eliminar_grupo(grupo_id: int, actor: dict = gestion):
    if estudiantes.listar(filtros={"grupo_id": grupo_id}, limite=1):
        raise HTTPException(status_code=409,
                            detail="No se puede desactivar: el grupo tiene estudiantes activos. Muévelos primero.")
    if not repo.desactivar(grupo_id):
        raise no_encontrado("Grupo")
    return {"mensaje": "Grupo desactivado correctamente (borrado lógico)."}


@router.post("/{grupo_id}/reactivar", response_model=Modelos.Mensaje)
def reactivar_grupo(grupo_id: int, actor: dict = gestion):
    if not repo.reactivar(grupo_id):
        raise no_encontrado("Grupo inactivo")
    return {"mensaje": "Grupo reactivado correctamente."}
