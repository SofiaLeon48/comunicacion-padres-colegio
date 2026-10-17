"""Tabla mensajes."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Mensaje(BaseModel):
    """Mensajes del chat de un grupo o directos entre dos usuarios."""
    # --- automáticos (los asigna la base de datos o la API; se ignoran si llegan) ---
    id: int | None = None
    remitente_id: int | None = None
    leido: bool | None = None
    fecha_envio: datetime | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan (grupo_id O destinatario_id, solo uno) ---
    grupo_id: int | None = Field(None, description="Para el chat del grupo")
    destinatario_id: int | None = Field(None, description="Para un mensaje directo")
    contenido: str | None = Field(None, min_length=1, max_length=2000)
    # --- datos relacionados que trae la consulta (solo lectura) ---
    remitente_nombre: str | None = None
    remitente_rol: str | None = None
