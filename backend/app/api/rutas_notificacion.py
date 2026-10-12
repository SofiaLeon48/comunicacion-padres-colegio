from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.core.deps import GESTION, UsuarioActual, no_encontrado, requiere_roles
from app.models.comun import Mensaje
from app.models.notificacion import ContadorNoLeidas, NotificacionCrear, NotificacionSalida
from app.repositories.notificacion_repo import NotificacionRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services import actividad
from app.services.notificador import notificar

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])
repo = NotificacionRepository()
usuarios = UsuarioRepository()


@router.get("/", response_model=list[NotificacionSalida], summary="Mis notificaciones")
def mis_notificaciones(usuario: UsuarioActual, solo_no_leidas: bool = False, limite: int = 50):
    return repo.de_usuario(usuario["id"], solo_no_leidas, limite)


@router.get("/contador", response_model=ContadorNoLeidas, summary="Cantidad sin leer (para la campanita)")
def contador(usuario: UsuarioActual):
    return {"no_leidas": repo.contar_no_leidas(usuario["id"])}


@router.patch("/leer-todas", response_model=Mensaje)
def leer_todas(usuario: UsuarioActual):
    n = repo.marcar_todas_leidas(usuario["id"])
    return {"mensaje": f"{n} notificaciones marcadas como leídas."}


@router.patch("/{notificacion_id}/leer", response_model=NotificacionSalida)
def leer(notificacion_id: int, usuario: UsuarioActual):
    n = repo.marcar_leida(notificacion_id, usuario["id"])
    if not n:
        raise no_encontrado("Notificación")
    return n


@router.post("/", response_model=Mensaje, status_code=201, summary="Enviar aviso del sistema")
def enviar_aviso(datos: NotificacionCrear, tareas: BackgroundTasks,
                 actor: dict = Depends(requiere_roles(*GESTION))):
    """Envía un aviso manual a usuarios puntuales (`usuario_ids`) o a roles completos (`roles`)."""
    ids = set(datos.usuario_ids or [])
    if datos.roles:
        ids |= set(usuarios.ids_por_roles(list(datos.roles)))
    if not ids:
        raise HTTPException(status_code=400, detail="Indica al menos un destinatario (usuario_ids o roles).")
    filas = notificar(list(ids), "sistema", datos.titulo, datos.contenido, por_correo=True, tareas=tareas)
    actividad.registrar(actor, "enviar_aviso", "notificaciones", None, f"{datos.titulo} → {len(filas)}")
    return {"mensaje": f"Aviso enviado a {len(filas)} usuarios."}


@router.delete("/{notificacion_id}", response_model=Mensaje)
def eliminar(notificacion_id: int, usuario: UsuarioActual):
    n = repo.obtener(notificacion_id)
    if not n or n["usuario_id"] != usuario["id"]:
        raise no_encontrado("Notificación")
    repo.desactivar(notificacion_id)
    return {"mensaje": "Notificación eliminada."}
