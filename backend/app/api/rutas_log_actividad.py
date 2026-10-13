from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.core.deps import GESTION, requiere_roles, requiere_modulo
from app.models.log_actividad import LogSalida
from app.repositories.log_actividad_repo import LogActividadRepository

router = APIRouter(prefix="/logs", tags=["Reportes y Analítica - logs de actividad"],
                   dependencies=[Depends(requiere_roles(*GESTION)), Depends(requiere_modulo("reportes"))])
repo = LogActividadRepository()


@router.get("/", response_model=list[LogSalida])
def listar_logs(usuario_id: int | None = None, entidad: str | None = None, accion: str | None = None,
                desde: datetime | None = None, hasta: datetime | None = None,
                limite: int = Query(100, le=500)):
    """Bitácora de auditoría. La API la llena sola en cada crear/actualizar/eliminar/login."""
    return repo.listar_detallado(usuario_id, entidad, accion, desde, hasta, limite)
