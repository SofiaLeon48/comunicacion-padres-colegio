"""Registro automático de auditoría en logs_actividad."""
import logging

from app.repositories.log_actividad_repo import LogActividadRepository

_logs = LogActividadRepository()
log = logging.getLogger("actividad")


def registrar(usuario: dict | None, accion: str, entidad: str,
              entidad_id: int | None = None, detalle: str | None = None) -> None:
    try:
        _logs.registrar(usuario["id"] if usuario else None, accion, entidad, entidad_id, detalle)
    except Exception as e:  # la auditoría nunca debe impedir la operación principal
        log.warning("No se pudo registrar actividad: %s", e)
