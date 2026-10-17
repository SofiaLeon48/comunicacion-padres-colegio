from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.core.config import a_hora_local, ahora_local
from app.core.deps import (PERSONAL, UsuarioActual, es_gestion, no_encontrado, prohibido, requiere_modulo,
                           requiere_roles)
from app.core.validacion import campos, obligatorios
from app.models.asistencia_citacion import AsistenciaCitacion
from app.models.citacion import Citacion
from app.repositories.asistencia_citacion_repo import AsistenciaCitacionRepository
from app.repositories.citacion_repo import CitacionRepository
from app.repositories.estudiante_repo import EstudianteRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services.notificador import notificar

router = APIRouter(prefix="/citaciones", tags=["Comunicados y Mensajería - citaciones"],
                   dependencies=[Depends(requiere_modulo("citaciones"))])
repo = CitacionRepository()
asistencias = AsistenciaCitacionRepository()
estudiantes = EstudianteRepository()
usuarios = UsuarioRepository()
personal = Depends(requiere_roles(*PERSONAL))


def _obtener_visible(citacion_id: int, usuario: dict) -> dict:
    c = repo.obtener_detallado(citacion_id)
    if not c:
        raise no_encontrado("Citación")
    if usuario["rol"] == "acudiente" and usuario["id"] not in repo.ids_acudientes_destino(c):
        raise no_encontrado("Citación")
    if usuario["rol"] == "docente" and c["docente_id"] != usuario["id"]:
        raise no_encontrado("Citación")
    return c


def _puede_gestionar(c: dict, usuario: dict) -> bool:
    return es_gestion(usuario) or c["docente_id"] == usuario["id"]


def _fecha(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y %I:%M %p")


@router.get("/", response_model=list[Citacion])
def listar_citaciones(usuario: UsuarioActual, desde: datetime | None = None, hasta: datetime | None = None,
                      estudiante_id: int | None = None, estado_citacion: str | None = None):
    """Usa `desde` y `hasta` para alimentar el **calendario** (ej. un mes).
    Cada rol ve lo suyo: acudiente → citaciones de sus hijos · docente → las que agendó ·
    coordinación/admin → todas."""
    docente_id = usuario["id"] if usuario["rol"] == "docente" else None
    acudiente_id = usuario["id"] if usuario["rol"] == "acudiente" else None
    return repo.listar_detallado(desde, hasta, docente_id, acudiente_id, estudiante_id, estado_citacion)


@router.get("/{citacion_id}", response_model=Citacion)
def obtener_citacion(citacion_id: int, usuario: UsuarioActual):
    return _obtener_visible(citacion_id, usuario)


@router.post("/", response_model=Citacion, status_code=201)
def crear_citacion(datos: Citacion, tareas: BackgroundTasks, actor: dict = personal):
    """Agenda la cita y notifica a los acudientes del estudiante (o al acudiente indicado)."""
    obligatorios(datos, "estudiante_id", "motivo", "fecha_hora")
    datos.fecha_hora = a_hora_local(datos.fecha_hora)
    est = estudiantes.obtener(datos.estudiante_id)
    if not est:
        raise HTTPException(status_code=400, detail="El estudiante no existe o está inactivo.")
    if datos.acudiente_id and not estudiantes.es_acudiente_de(datos.acudiente_id, datos.estudiante_id):
        raise HTTPException(status_code=400, detail="Ese acudiente no está vinculado al estudiante.")
    if datos.fecha_hora <= ahora_local():
        raise HTTPException(status_code=400, detail="La citación debe ser en una fecha futura.")

    docente_id = actor["id"]
    if datos.docente_id and datos.docente_id != actor["id"]:
        if not es_gestion(actor):
            raise prohibido("Solo coordinación puede agendar a nombre de otro docente.")
        docente_id = datos.docente_id

    nueva = repo.crear({**campos(datos, "estudiante_id", "acudiente_id", "motivo", "fecha_hora", "lugar"),
                       "docente_id": docente_id})
    destino = repo.ids_acudientes_destino(nueva)
    notificar(destino, "citacion", f"Citación: {est['nombre']}",
              f"{datos.motivo} · {_fecha(datos.fecha_hora)}" + (f" · {datos.lugar}" if datos.lugar else ""),
              referencia_id=nueva["id"], por_correo=True, tareas=tareas)
    return repo.obtener_detallado(nueva["id"])


@router.patch("/{citacion_id}", response_model=Citacion)
def actualizar_citacion(citacion_id: int, datos: Citacion, tareas: BackgroundTasks,
                        actor: dict = personal):
    c = _obtener_visible(citacion_id, actor)
    if not _puede_gestionar(c, actor):
        raise prohibido()
    valores = campos(datos, "motivo", "fecha_hora", "lugar", "acudiente_id", editar=True)
    if valores.get("fecha_hora"):
        valores["fecha_hora"] = a_hora_local(valores["fecha_hora"])
    if valores.get("fecha_hora") and valores["fecha_hora"] <= ahora_local():
        raise HTTPException(status_code=400, detail="La citación debe ser en una fecha futura.")
    if "acudiente_id" in valores and valores["acudiente_id"] and \
            not estudiantes.es_acudiente_de(valores["acudiente_id"], c["estudiante_id"]):
        raise HTTPException(status_code=400, detail="Ese acudiente no está vinculado al estudiante.")
    repo.actualizar(citacion_id, valores)
    actualizada = repo.obtener_detallado(citacion_id)
    if "fecha_hora" in valores and actualizada:
        notificar(repo.ids_acudientes_destino(actualizada), "citacion",
                  f"Citación reprogramada: {actualizada['estudiante_nombre']}",
                  f"Nueva fecha: {_fecha(actualizada['fecha_hora'])}", citacion_id, True, tareas)
    return actualizada or repo.obtener(citacion_id, True)


@router.patch("/{citacion_id}/estado", response_model=Citacion, summary="Confirmar / cancelar / realizar")
def cambiar_estado(citacion_id: int, datos: Citacion, usuario: UsuarioActual):
    """- **Acudiente**: solo puede pasarla a `confirmada` (confirma que asistirá).
    - **Docente dueño / coordinación**: cualquier estado (`cancelada` notifica a los acudientes)."""
    obligatorios(datos, "estado_citacion")
    c = _obtener_visible(citacion_id, usuario)
    nuevo = datos.estado_citacion
    if c["estado_citacion"] in ("cancelada", "realizada"):
        raise HTTPException(status_code=400, detail=f"La citación ya está {c['estado_citacion']}.")
    if usuario["rol"] == "acudiente":
        if nuevo != "confirmada":
            raise prohibido("Como acudiente solo puedes confirmar tu asistencia.")
    elif not _puede_gestionar(c, usuario):
        raise prohibido()

    repo.actualizar(citacion_id, {"estado_citacion": nuevo})
    if usuario["rol"] == "acudiente":
        notificar([c["docente_id"]], "citacion", "Citación confirmada",
                  f"{usuario['nombre']} confirmó la cita de {c['estudiante_nombre']}", citacion_id)
    elif nuevo == "cancelada":
        notificar(repo.ids_acudientes_destino(c), "citacion", f"Citación cancelada: {c['estudiante_nombre']}",
                  f"Se canceló la cita del {_fecha(c['fecha_hora'])}", citacion_id)
    return repo.obtener_detallado(citacion_id)


@router.delete("/{citacion_id}")
def eliminar_citacion(citacion_id: int, actor: dict = personal):
    c = _obtener_visible(citacion_id, actor)
    if not _puede_gestionar(c, actor):
        raise prohibido()
    repo.desactivar(citacion_id)
    return {"mensaje": "Citación eliminada correctamente (borrado lógico)."}


# ------------------------------------------------- asistencia (relación 1:1)
@router.get("/{citacion_id}/asistencia", response_model=AsistenciaCitacion)
def obtener_asistencia(citacion_id: int, usuario: UsuarioActual):
    _obtener_visible(citacion_id, usuario)
    a = asistencias.de_citacion(citacion_id)
    if not a:
        raise no_encontrado("Registro de asistencia")
    return a


@router.post("/{citacion_id}/asistencia", response_model=AsistenciaCitacion, status_code=201,
             summary="Registrar si el acudiente asistió (marca la citación como realizada)")
def registrar_asistencia(citacion_id: int, datos: AsistenciaCitacion, actor: dict = personal):
    obligatorios(datos, "asistio")
    c = _obtener_visible(citacion_id, actor)
    if not _puede_gestionar(c, actor):
        raise prohibido()
    if c["estado_citacion"] == "cancelada":
        raise HTTPException(status_code=400, detail="No se registra asistencia en una citación cancelada.")
    a = asistencias.crear({**campos(datos, "asistio", "observaciones"), "citacion_id": citacion_id,
                          "registrado_por": actor["id"]})
    repo.actualizar(citacion_id, {"estado_citacion": "realizada"})
    return a


@router.patch("/{citacion_id}/asistencia", response_model=AsistenciaCitacion)
def actualizar_asistencia(citacion_id: int, datos: AsistenciaCitacion, actor: dict = personal):
    c = _obtener_visible(citacion_id, actor)
    if not _puede_gestionar(c, actor):
        raise prohibido()
    a = asistencias.de_citacion(citacion_id)
    if not a:
        raise no_encontrado("Registro de asistencia")
    return asistencias.actualizar(a["id"], campos(datos, "asistio", "observaciones", editar=True))
