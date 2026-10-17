"""Tabla grupos."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Grupo(BaseModel):
    """Grupos del colegio (ej. 5A), con su jornada, año lectivo y director."""
    # --- automáticos (los asigna la base de datos; se ignoran si llegan) ---
    id: int | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan ---
    nombre: str | None = Field(None, min_length=1, max_length=20, examples=["5A"])
    grado: int | None = Field(None, ge=0, le=11, examples=[5])
    jornada: Literal["manana", "tarde", "unica"] | None = Field(None, description="Vacío = mañana")
    anio_lectivo: int | None = Field(None, ge=2000, le=2100, description="Vacío = año actual")
    director_id: int | None = None
    # --- datos relacionados que trae la consulta (solo lectura) ---
    director_nombre: str | None = None
    total_estudiantes: int | None = None
