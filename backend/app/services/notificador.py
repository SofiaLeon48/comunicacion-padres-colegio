"""
Servicio de notificaciones: el punto único por donde pasa todo aviso.

1. Guarda una fila en la tabla notificaciones por cada destinatario.
2. La empuja en tiempo real por WebSocket a quien esté conectado.
3. (Opcional) Envía correo en segundo plano y marca enviado_correo = TRUE.
"""
from fastapi import BackgroundTasks

from app.repositories.notificacion_repo import NotificacionRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services.correo import correo_habilitado, enviar_correo
from app.services.tiempo_real import gestor

_notificaciones = NotificacionRepository()
_usuarios = UsuarioRepository()


def notificar(usuario_ids: list[int], tipo: str, titulo: str, contenido: str,
              referencia_id: int | None = None, por_correo: bool = False,
              tareas: BackgroundTasks | None = None) -> list[dict]:
    filas = _notificaciones.crear_para_varios(usuario_ids, tipo, titulo, contenido, referencia_id)
    for fila in filas:
        gestor.enviar([fila["usuario_id"]], "notificacion", fila)
    if por_correo and correo_habilitado() and filas:
        if tareas is not None:
            tareas.add_task(_enviar_correos, filas, titulo, contenido)
        else:
            _enviar_correos(filas, titulo, contenido)
    return filas


def _enviar_correos(filas: list[dict], titulo: str, contenido: str) -> None:
    correos = []
    for fila in filas:
        u = _usuarios.obtener(fila["usuario_id"])
        if u:
            correos.append(u["correo"])
    if enviar_correo(correos, f"[Colegio] {titulo}", contenido):
        _notificaciones.marcar_correo_enviado([f["id"] for f in filas])
