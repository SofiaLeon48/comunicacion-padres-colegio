"""Tabla notificaciones."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Notificacion(BaseModel):
    """Avisos que recibe cada usuario (los crea la API automáticamente)."""
    id: int | None = None
    usuario_id: int | None = None
    tipo: Literal["comunicado", "mensaje", "citacion", "sistema"] | None = None
    titulo: str | None = None
    contenido: str | None = None
    referencia_id: int | None = None
    leido: bool | None = None
    enviado_correo: bool | None = None
    fecha: datetime | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
