from fastapi import APIRouter, Depends

from app.core.deps import GESTION, UsuarioActual, no_encontrado, prohibido, requiere_roles, requiere_modulo
from app.core.validacion import campos, obligatorios
from app.models.estudiante import Estudiante
from app.repositories.estudiante_repo import EstudianteRepository

router = APIRouter(prefix="/estudiantes", tags=["Administración - estudiantes"],
                   dependencies=[Depends(requiere_modulo("estudiantes"))])
repo = EstudianteRepository()
gestion = Depends(requiere_roles(*GESTION))


@router.get("/", response_model=list[Estudiante])
def listar_estudiantes(usuario: UsuarioActual, grupo_id: int | None = None, buscar: str | None = None,
                       incluir_inactivos: bool = False):
    """Un acudiente solo ve a sus propios hijos."""
    acudiente_id = usuario["id"] if usuario["rol"] == "acudiente" else None
    return repo.listar_detallado(grupo_id, acudiente_id, buscar, incluir_inactivos)


@router.get("/{estudiante_id}", response_model=Estudiante)
def obtener_estudiante(estudiante_id: int, usuario: UsuarioActual):
    acudiente_id = usuario["id"] if usuario["rol"] == "acudiente" else None
    est = next((e for e in repo.listar_detallado(acudiente_id=acudiente_id) if e["id"] == estudiante_id), None)
    if not est:
        raise no_encontrado("Estudiante")
    return est


@router.get("/{estudiante_id}/acudientes")
def acudientes_del_estudiante(estudiante_id: int, usuario: UsuarioActual):
    if usuario["rol"] == "acudiente" and not repo.es_acudiente_de(usuario["id"], estudiante_id):
        raise prohibido()
    return repo.acudientes(estudiante_id)


@router.post("/", response_model=Estudiante, status_code=201)
def crear_estudiante(datos: Estudiante, actor: dict = gestion):
    obligatorios(datos, "nombre", "documento", "grupo_id")
    est = repo.crear(campos(datos, "nombre", "documento", "grupo_id"))
    return est


@router.patch("/{estudiante_id}", response_model=Estudiante)
def actualizar_estudiante(estudiante_id: int, datos: Estudiante, actor: dict = gestion):
    est = repo.actualizar(estudiante_id, campos(datos, "nombre", "documento", "grupo_id", editar=True))
    if not est:
        raise no_encontrado("Estudiante")
    return est


@router.delete("/{estudiante_id}")
def eliminar_estudiante(estudiante_id: int, actor: dict = gestion):
    if not repo.desactivar(estudiante_id):
        raise no_encontrado("Estudiante")
    return {"mensaje": "Estudiante desactivado correctamente (borrado lógico)."}


@router.post("/{estudiante_id}/reactivar")
def reactivar_estudiante(estudiante_id: int, actor: dict = gestion):
    if not repo.reactivar(estudiante_id):
        raise no_encontrado("Estudiante inactivo")
    return {"mensaje": "Estudiante reactivado correctamente."}
