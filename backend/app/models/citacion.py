"""Tabla citaciones."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Citacion(BaseModel):
    """Citas de un docente con los acudientes de un estudiante."""
    # --- automáticos (los asigna la base de datos; se ignoran si llegan) ---
    id: int | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan ---
    estudiante_id: int | None = None
    docente_id: int | None = Field(None, description="Vacío = quien agenda. Solo coordinación cita a nombre de otro")
    acudiente_id: int | None = Field(None, description="Vacío = todos los acudientes del estudiante")
    motivo: str | None = Field(None, min_length=3, max_length=255, examples=["Seguimiento académico"])
    fecha_hora: datetime | None = Field(None, examples=["2026-10-20T07:30:00"])
    lugar: str | None = Field(None, max_length=100, examples=["Sala de profesores"])
    estado_citacion: Literal["pendiente", "confirmada", "cancelada", "realizada"] | None = None
    # --- datos relacionados que trae la consulta (solo lectura) ---
    estudiante_nombre: str | None = None
    grupo_nombre: str | None = None
    docente_nombre: str | None = None
    acudiente_nombre: str | None = None
    asistio: bool | None = None
    observaciones: str | None = None
