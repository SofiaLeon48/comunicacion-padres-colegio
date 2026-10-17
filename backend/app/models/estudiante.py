"""Tabla estudiantes."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Estudiante(BaseModel):
    """Estudiantes matriculados en un grupo."""
    # --- automáticos (los asigna la base de datos; se ignoran si llegan) ---
    id: int | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan ---
    nombre: str | None = Field(None, min_length=3, max_length=100, examples=["Juan Pérez"])
    documento: str | None = Field(None, min_length=4, max_length=20, examples=["1043000111"])
    grupo_id: int | None = None
    # --- datos relacionados que trae la consulta (solo lectura) ---
    grupo_nombre: str | None = None
    grupo_jornada: str | None = None
    director_nombre: str | None = None
    acudientes: str | None = None
