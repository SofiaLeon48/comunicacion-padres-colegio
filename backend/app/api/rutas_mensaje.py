from fastapi import APIRouter, HTTPException, Query

from app.core.deps import UsuarioActual, es_gestion, no_encontrado, prohibido
from app.models.comun import Mensaje
from app.models.mensaje import Conversacion, MensajeCrear, MensajeEditar, MensajeSalida
from app.repositories.curso_repo import CursoRepository
from app.repositories.mensaje_repo import MensajeRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services import actividad
from app.services.notificador import notificar
from app.services.tiempo_real import gestor

router = APIRouter(prefix="/mensajes", tags=["Comunicados y Mensajería - mensajes"])
repo = MensajeRepository()
cursos = CursoRepository()
usuarios = UsuarioRepository()


def _verificar_acceso_curso(curso_id: int, usuario: dict) -> None:
    if not cursos.obtener(curso_id):
        raise no_encontrado("Curso")
    if usuario["rol"] == "acudiente" and not cursos.acudiente_pertenece(curso_id, usuario["id"]):
        raise prohibido("Solo puedes participar en el chat de los cursos de tus hijos.")


@router.get("/curso/{curso_id}", response_model=list[MensajeSalida], summary="Chat de un curso")
def chat_del_curso(curso_id: int, usuario: UsuarioActual, limite: int = Query(50, le=200),
                   antes_de: int | None = Query(None, description="Para cargar mensajes más antiguos")):
    _verificar_acceso_curso(curso_id, usuario)
    return repo.del_curso(curso_id, limite, antes_de)


@router.get("/directos", response_model=list[Conversacion], summary="Mi bandeja de mensajes directos")
def bandeja(usuario: UsuarioActual):
    return repo.bandeja(usuario["id"])


@router.get("/directos/{otro_usuario_id}", response_model=list[MensajeSalida],
            summary="Conversación con un usuario (la marca como leída)")
def conversacion(otro_usuario_id: int, usuario: UsuarioActual, limite: int = Query(50, le=200)):
    mensajes = repo.conversacion(usuario["id"], otro_usuario_id, limite)
    if repo.marcar_leidos(otro_usuario_id, usuario["id"]):
        gestor.enviar([otro_usuario_id], "mensajes_leidos", {"por": usuario["id"]})
    return mensajes


@router.post("/", response_model=MensajeSalida, status_code=201)
def enviar_mensaje(datos: MensajeCrear, usuario: UsuarioActual):
    """Envía al chat del curso (`curso_id`) o un mensaje directo (`destinatario_id`).
    Se entrega en tiempo real por WebSocket a los destinatarios conectados."""
    if datos.curso_id is not None:
        _verificar_acceso_curso(datos.curso_id, usuario)
    else:
        dest = usuarios.obtener_con_rol(datos.destinatario_id)
        if not dest:
            raise HTTPException(status_code=400, detail="El destinatario no existe o está inactivo.")
        if usuario["rol"] == "acudiente" and dest["rol"] == "acudiente":
            raise prohibido("Los acudientes solo pueden escribir directamente al personal del colegio.")

    nuevo = repo.crear({**datos.model_dump(), "remitente_id": usuario["id"]})
    mensaje = repo.obtener_detallado(nuevo["id"])

    if datos.curso_id is not None:
        gestor.enviar(cursos.ids_miembros(datos.curso_id) + [usuario["id"]], "mensaje", mensaje)
    else:
        gestor.enviar([datos.destinatario_id, usuario["id"]], "mensaje", mensaje)
        notificar([datos.destinatario_id], "mensaje", f"Nuevo mensaje de {usuario['nombre']}",
                  datos.contenido[:250], referencia_id=nuevo["id"])
    actividad.registrar(usuario, "enviar_mensaje", "mensajes", nuevo["id"])
    return mensaje


@router.patch("/{mensaje_id}", response_model=MensajeSalida, summary="Editar mi mensaje")
def editar_mensaje(mensaje_id: int, datos: MensajeEditar, usuario: UsuarioActual):
    m = repo.obtener(mensaje_id)
    if not m:
        raise no_encontrado("Mensaje")
    if m["remitente_id"] != usuario["id"]:
        raise prohibido("Solo puedes editar tus propios mensajes.")
    repo.actualizar(mensaje_id, {"contenido": datos.contenido})
    return repo.obtener_detallado(mensaje_id)


@router.delete("/{mensaje_id}", response_model=Mensaje)
def eliminar_mensaje(mensaje_id: int, usuario: UsuarioActual):
    m = repo.obtener(mensaje_id)
    if not m:
        raise no_encontrado("Mensaje")
    if m["remitente_id"] != usuario["id"] and not es_gestion(usuario):
        raise prohibido("Solo el remitente o coordinación pueden eliminar este mensaje.")
    repo.desactivar(mensaje_id)
    actividad.registrar(usuario, "eliminar", "mensajes", mensaje_id)
    return {"mensaje": "Mensaje eliminado correctamente."}
