"""Tabla roles."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Rol(BaseModel):
    """Tipos de usuario: coordinacion, docente, acudiente."""
    # --- automáticos (los asigna la base de datos; se ignoran si llegan) ---
    id: int | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan ---
    nombre: str | None = Field(None, min_length=3, max_length=30, examples=["docente"])
    descripcion: str | None = Field(None, max_length=150)
