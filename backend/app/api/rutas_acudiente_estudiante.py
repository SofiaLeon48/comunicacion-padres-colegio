from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import GESTION, UsuarioActual, no_encontrado, requiere_roles, requiere_modulo
from app.models.modelos import Modelos
from app.repositories.acudiente_estudiante_repo import AcudienteEstudianteRepository
from app.repositories.usuario_repo import UsuarioRepository

router = APIRouter(prefix="/acudientes-estudiantes", tags=["Administración - vínculos acudiente/estudiante"],
                   dependencies=[Depends(requiere_modulo("estudiantes"))])
repo = AcudienteEstudianteRepository()
usuarios = UsuarioRepository()
gestion = Depends(requiere_roles(*GESTION))


def _detalle(vinculo_id: int) -> dict | None:
    return next((v for v in repo.listar_detallado(incluir_inactivos=True) if v["id"] == vinculo_id), None)


@router.get("/", response_model=list[Modelos.VinculoSalida])
def listar_vinculos(usuario: UsuarioActual, acudiente_id: int | None = None, estudiante_id: int | None = None,
                    incluir_inactivos: bool = False):
    if usuario["rol"] == "acudiente":
        acudiente_id = usuario["id"]
    return repo.listar_detallado(acudiente_id, estudiante_id, incluir_inactivos)


@router.post("/", response_model=Modelos.VinculoSalida, status_code=201)
def crear_vinculo(datos: Modelos.VinculoCrear, actor: dict = gestion):
    acudiente = usuarios.obtener_con_rol(datos.acudiente_id)
    if not acudiente or acudiente["rol"] != "acudiente":
        raise HTTPException(status_code=400, detail="El usuario indicado no es un acudiente activo.")
    # Si el vínculo existía y fue desactivado, se reactiva en lugar de duplicarlo
    previo = next((v for v in repo.listar_detallado(datos.acudiente_id, datos.estudiante_id, True)
                   if v["estado"] == "inactivo"), None)
    if previo:
        repo.actualizar(previo["id"], {**datos.model_dump(), "estado": "activo"})
        return _detalle(previo["id"])
    vinculo = repo.crear(datos.model_dump())
    return _detalle(vinculo["id"])


@router.patch("/{vinculo_id}", response_model=Modelos.VinculoSalida)
def actualizar_vinculo(vinculo_id: int, datos: Modelos.VinculoActualizar, actor: dict = gestion):
    if not repo.actualizar(vinculo_id, datos.model_dump(exclude_unset=True)):
        raise no_encontrado("Vínculo")
    return _detalle(vinculo_id)


@router.delete("/{vinculo_id}", response_model=Modelos.Mensaje)
def eliminar_vinculo(vinculo_id: int, actor: dict = gestion):
    if not repo.desactivar(vinculo_id):
        raise no_encontrado("Vínculo")
    return {"mensaje": "Vínculo desactivado correctamente."}
