from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import GESTION, UsuarioActual, no_encontrado, prohibido, requiere_roles
from app.models.comun import Mensaje
from app.models.curso import CursoActualizar, CursoCrear, CursoSalida
from app.models.estudiante import EstudianteSalida
from app.repositories.curso_repo import CursoRepository
from app.repositories.estudiante_repo import EstudianteRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services import actividad

router = APIRouter(prefix="/cursos", tags=["Administración - cursos"])
repo = CursoRepository()
estudiantes = EstudianteRepository()
usuarios = UsuarioRepository()
gestion = Depends(requiere_roles(*GESTION))


def _validar_director(director_id: int | None) -> None:
    if director_id is None:
        return
    u = usuarios.obtener_con_rol(director_id)
    if not u or u["rol"] not in ("docente", "coordinacion"):
        raise HTTPException(status_code=400, detail="El director de grupo debe ser un docente activo.")


@router.get("/", response_model=list[CursoSalida])
def listar_cursos(usuario: UsuarioActual, anio_lectivo: int | None = None, incluir_inactivos: bool = False):
    """Un acudiente solo ve los cursos donde tiene hijos matriculados."""
    acudiente_id = usuario["id"] if usuario["rol"] == "acudiente" else None
    return repo.listar_detallado(acudiente_id, anio_lectivo, incluir_inactivos)


@router.get("/{curso_id}", response_model=CursoSalida)
def obtener_curso(curso_id: int, usuario: UsuarioActual):
    acudiente_id = usuario["id"] if usuario["rol"] == "acudiente" else None
    curso = next((c for c in repo.listar_detallado(acudiente_id) if c["id"] == curso_id), None)
    if not curso:
        raise no_encontrado("Curso")
    return curso


@router.get("/{curso_id}/estudiantes", response_model=list[EstudianteSalida])
def estudiantes_del_curso(curso_id: int, usuario: UsuarioActual):
    if usuario["rol"] == "acudiente":
        raise prohibido()
    return estudiantes.listar_detallado(curso_id=curso_id)


@router.post("/", response_model=CursoSalida, status_code=201)
def crear_curso(datos: CursoCrear, actor: dict = gestion):
    _validar_director(datos.director_id)
    curso = repo.crear(datos.model_dump(exclude_none=True))
    actividad.registrar(actor, "crear", "cursos", curso["id"], curso["nombre"])
    return curso


@router.patch("/{curso_id}", response_model=CursoSalida)
def actualizar_curso(curso_id: int, datos: CursoActualizar, actor: dict = gestion):
    valores = datos.model_dump(exclude_unset=True)
    _validar_director(valores.get("director_id"))
    curso = repo.actualizar(curso_id, valores)
    if not curso:
        raise no_encontrado("Curso")
    actividad.registrar(actor, "actualizar", "cursos", curso_id)
    return curso


@router.delete("/{curso_id}", response_model=Mensaje)
def eliminar_curso(curso_id: int, actor: dict = gestion):
    if estudiantes.listar(filtros={"curso_id": curso_id}, limite=1):
        raise HTTPException(status_code=409,
                            detail="No se puede desactivar: el curso tiene estudiantes activos. Muévelos primero.")
    if not repo.desactivar(curso_id):
        raise no_encontrado("Curso")
    actividad.registrar(actor, "eliminar", "cursos", curso_id)
    return {"mensaje": "Curso desactivado correctamente (borrado lógico)."}


@router.post("/{curso_id}/reactivar", response_model=Mensaje)
def reactivar_curso(curso_id: int, actor: dict = gestion):
    if not repo.reactivar(curso_id):
        raise no_encontrado("Curso inactivo")
    actividad.registrar(actor, "reactivar", "cursos", curso_id)
    return {"mensaje": "Curso reactivado correctamente."}
