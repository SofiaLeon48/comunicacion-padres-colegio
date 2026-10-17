from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException

from app.core.deps import GESTION, UsuarioActual, no_encontrado, requiere_roles
from app.models.notificacion import Notificacion
from app.repositories.notificacion_repo import NotificacionRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services.notificador import notificar

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])
repo = NotificacionRepository()
usuarios = UsuarioRepository()


@router.get("/", response_model=list[Notificacion], summary="Mis notificaciones")
def mis_notificaciones(usuario: UsuarioActual, solo_no_leidas: bool = False, limite: int = 50):
    return repo.de_usuario(usuario["id"], solo_no_leidas, limite)


@router.get("/contador", summary="Cantidad sin leer (para la campanita)")
def contador(usuario: UsuarioActual):
    return {"no_leidas": repo.contar_no_leidas(usuario["id"])}


@router.patch("/leer-todas")
def leer_todas(usuario: UsuarioActual):
    n = repo.marcar_todas_leidas(usuario["id"])
    return {"mensaje": f"{n} notificaciones marcadas como leídas."}


@router.patch("/{notificacion_id}/leer", response_model=Notificacion)
def leer(notificacion_id: int, usuario: UsuarioActual):
    n = repo.marcar_leida(notificacion_id, usuario["id"])
    if not n:
        raise no_encontrado("Notificación")
    return n


@router.post("/", status_code=201, summary="Enviar aviso del sistema")
def enviar_aviso(tareas: BackgroundTasks,
                 titulo: str = Body(min_length=3, max_length=150),
                 contenido: str = Body(min_length=1, max_length=255),
                 usuario_ids: list[int] | None = Body(None, description="Destinatarios puntuales"),
                 roles: list[Literal["coordinacion", "docente", "acudiente"]] | None = Body(None, description="O roles completos"),
                 actor: dict = Depends(requiere_roles(*GESTION))):
    """Envía un aviso manual a usuarios puntuales (`usuario_ids`) o a roles completos (`roles`)."""
    ids = set(usuario_ids or [])
    if roles:
        ids |= set(usuarios.ids_por_roles(list(roles)))
    if not ids:
        raise HTTPException(status_code=400, detail="Indica al menos un destinatario (usuario_ids o roles).")
    filas = notificar(list(ids), "sistema", titulo, contenido, por_correo=True, tareas=tareas)
    return {"mensaje": f"Aviso enviado a {len(filas)} usuarios."}


@router.delete("/{notificacion_id}")
def eliminar(notificacion_id: int, usuario: UsuarioActual):
    n = repo.obtener(notificacion_id)
    if not n or n["usuario_id"] != usuario["id"]:
        raise no_encontrado("Notificación")
    repo.desactivar(notificacion_id)
    return {"mensaje": "Notificación eliminada."}
