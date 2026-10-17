"""Tabla comunicados."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Comunicado(BaseModel):
    """Circulares para un grupo o para todo el colegio."""
    # --- automáticos (los asigna la base de datos o la API; se ignoran si llegan) ---
    id: int | None = None
    autor_id: int | None = None
    fecha_publicacion: datetime | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan ---
    titulo: str | None = Field(None, min_length=3, max_length=150, examples=["Reunión de padres"])
    contenido: str | None = Field(None, min_length=1, examples=["Se cita a reunión general el viernes..."])
    grupo_id: int | None = Field(None, description="Vacío = circular para todo el colegio")
    prioridad: Literal["normal", "urgente"] | None = Field(None, description="Vacío = normal")
    requiere_confirmacion: bool | None = Field(None, description="Vacío = sí")
    # --- datos relacionados que trae la consulta (solo lectura) ---
    grupo_nombre: str | None = None
    autor_nombre: str | None = None
    confirmado_por_mi: bool | None = None
    total_confirmados: int | None = None
