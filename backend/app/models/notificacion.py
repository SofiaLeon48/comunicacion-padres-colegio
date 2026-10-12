from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.comun import Auditoria, NombreRol

TipoNotificacion = Literal["comunicado", "mensaje", "citacion", "sistema"]


class NotificacionCrear(BaseModel):
    """Aviso manual (tipo 'sistema') que envía administración o coordinación."""
    titulo: str = Field(min_length=3, max_length=150)
    contenido: str = Field(min_length=1, max_length=255)
    usuario_ids: list[int] | None = Field(default=None, description="Destinatarios puntuales")
    roles: list[NombreRol] | None = Field(default=None, description="O todos los usuarios de estos roles")


class NotificacionSalida(Auditoria):
    id: int
    usuario_id: int
    tipo: str
    titulo: str
    contenido: str
    referencia_id: int | None
    leido: bool
    enviado_correo: bool
    fecha: datetime


class ContadorNoLeidas(BaseModel):
    no_leidas: int
