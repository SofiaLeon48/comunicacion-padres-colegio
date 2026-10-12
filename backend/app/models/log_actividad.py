from datetime import datetime

from pydantic import BaseModel

from app.models.comun import Auditoria


class LogSalida(Auditoria):
    id: int
    usuario_id: int | None
    usuario_nombre: str | None = None
    accion: str
    entidad: str
    entidad_id: int | None
    detalle: str | None
    fecha: datetime
