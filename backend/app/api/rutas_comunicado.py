from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.core.deps import PERSONAL, UsuarioActual, es_gestion, no_encontrado, prohibido, requiere_roles, requiere_modulo
from app.core.validacion import campos, obligatorios
from app.models.confirmacion_lectura import ConfirmacionLectura
from app.models.comunicado import Comunicado
from app.repositories.comunicado_repo import ComunicadoRepository
from app.repositories.confirmacion_lectura_repo import ConfirmacionLecturaRepository
from app.repositories.grupo_repo import GrupoRepository
from app.services.notificador import notificar

router = APIRouter(prefix="/comunicados", tags=["Comunicados y Mensajería - comunicados"],
                   dependencies=[Depends(requiere_modulo("comunicados"))])
repo = ComunicadoRepository()
confirmaciones = ConfirmacionLecturaRepository()
grupos = GrupoRepository()


def _obtener_visible(comunicado_id: int, usuario: dict) -> dict:
    """Devuelve el comunicado si el usuario tiene derecho a verlo; si no, 404."""
    c = repo.obtener_detallado(comunicado_id, usuario["id"])
    if not c:
        raise no_encontrado("Comunicado")
    if usuario["rol"] == "acudiente" and not repo.es_destinatario(c["grupo_id"], usuario["id"]):
        raise no_encontrado("Comunicado")
    return c


def _puede_editar(c: dict, usuario: dict) -> bool:
    return es_gestion(usuario) or c["autor_id"] == usuario["id"]


@router.get("/", response_model=list[Comunicado])
def listar_comunicados(usuario: UsuarioActual, grupo_id: int | None = None, prioridad: str | None = None,
                       incluir_inactivos: bool = False):
    """Ordenados del más reciente al más antiguo. Incluye `confirmado_por_mi`.
    Un acudiente solo ve las circulares generales y las de los grupos de sus hijos."""
    return repo.listar_visibles(usuario["id"], usuario["rol"] == "acudiente", grupo_id, prioridad,
                                incluir_inactivos and es_gestion(usuario))


@router.get("/{comunicado_id}", response_model=Comunicado)
def obtener_comunicado(comunicado_id: int, usuario: UsuarioActual):
    return _obtener_visible(comunicado_id, usuario)


@router.post("/", response_model=Comunicado, status_code=201)
def crear_comunicado(datos: Comunicado, tareas: BackgroundTasks,
                     autor: dict = Depends(requiere_roles(*PERSONAL))):
    """Publica la circular y **notifica automáticamente** a todos los acudientes destinatarios
    (en la plataforma, en tiempo real y por correo si está configurado)."""
    obligatorios(datos, "titulo", "contenido")
    if datos.grupo_id is None and autor["rol"] == "docente":
        raise prohibido("Solo coordinación o administración pueden publicar circulares generales.")
    if datos.grupo_id is not None and not grupos.obtener(datos.grupo_id):
        raise HTTPException(status_code=400, detail="El grupo indicado no existe o está inactivo.")
    nuevo = repo.crear({**campos(datos, "titulo", "contenido", "grupo_id", "prioridad", "requiere_confirmacion"),
                        "autor_id": autor["id"]})

    destinatarios = [d["id"] for d in repo.destinatarios(nuevo["grupo_id"])]
    prefijo = "URGENTE: " if nuevo["prioridad"] == "urgente" else ""
    notificar(destinatarios, "comunicado", f"{prefijo}{nuevo['titulo']}",
              nuevo["contenido"][:250], referencia_id=nuevo["id"], por_correo=True, tareas=tareas)
    return repo.obtener_detallado(nuevo["id"], autor["id"])


@router.patch("/{comunicado_id}", response_model=Comunicado)
def actualizar_comunicado(comunicado_id: int, datos: Comunicado, usuario: UsuarioActual):
    c = repo.obtener(comunicado_id)
    if not c:
        raise no_encontrado("Comunicado")
    if not _puede_editar(c, usuario):
        raise prohibido("Solo el autor o coordinación pueden editar este comunicado.")
    repo.actualizar(comunicado_id, campos(datos, "titulo", "contenido", "prioridad", "requiere_confirmacion", editar=True))
    return repo.obtener_detallado(comunicado_id, usuario["id"]) or repo.obtener(comunicado_id, True)


@router.delete("/{comunicado_id}")
def eliminar_comunicado(comunicado_id: int, usuario: UsuarioActual):
    c = repo.obtener(comunicado_id)
    if not c:
        raise no_encontrado("Comunicado")
    if not _puede_editar(c, usuario):
        raise prohibido("Solo el autor o coordinación pueden eliminar este comunicado.")
    repo.desactivar(comunicado_id)
    return {"mensaje": "Comunicado archivado correctamente (borrado lógico)."}


# ------------------------------------------------------ confirmación de lectura
@router.post("/{comunicado_id}/confirmar", response_model=ConfirmacionLectura, status_code=201,
             summary="Confirmar lectura (acudiente)")
def confirmar_lectura(comunicado_id: int, usuario: UsuarioActual):
    c = _obtener_visible(comunicado_id, usuario)
    if usuario["rol"] != "acudiente":
        raise prohibido("Solo los acudientes destinatarios confirman lectura.")
    if not c["requiere_confirmacion"]:
        raise HTTPException(status_code=400, detail="Este comunicado no requiere confirmación.")
    conf = confirmaciones.crear({"comunicado_id": comunicado_id, "usuario_id": usuario["id"]})
    return conf


@router.get("/{comunicado_id}/lecturas",
            dependencies=[Depends(requiere_roles(*PERSONAL))],
            summary="Quién ha leído y quién no")
def estado_de_lectura(comunicado_id: int):
    c = repo.obtener(comunicado_id)
    if not c:
        raise no_encontrado("Comunicado")
    detalle = repo.estado_lectura(comunicado_id, c["grupo_id"])
    total = len(detalle)
    leidos = sum(1 for d in detalle if d["confirmado"])
    return {"comunicado_id": comunicado_id, "destinatarios": total, "confirmados": leidos,
            "porcentaje": round(100 * leidos / total, 1) if total else 0.0, "detalle": detalle}
