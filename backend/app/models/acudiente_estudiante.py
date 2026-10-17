"""Tabla acudiente_estudiante."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AcudienteEstudiante(BaseModel):
    """Vínculo entre un acudiente (usuario) y un estudiante."""
    # --- automáticos (los asigna la base de datos; se ignoran si llegan) ---
    id: int | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan ---
    acudiente_id: int | None = None
    estudiante_id: int | None = None
    parentesco: str | None = Field(None, max_length=30, examples=["madre"], description="Vacío = acudiente")
    es_principal: bool | None = None
    # --- datos relacionados que trae la consulta (solo lectura) ---
    acudiente_nombre: str | None = None
    estudiante_nombre: str | None = None
    grupo_nombre: str | None = None
