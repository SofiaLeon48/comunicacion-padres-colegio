"""Tabla asistencia_citaciones."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AsistenciaCitacion(BaseModel):
    """Resultado de una citación: si el acudiente asistió (relación 1:1)."""
    # --- automáticos (los asigna la base de datos o la API; se ignoran si llegan) ---
    id: int | None = None
    citacion_id: int | None = None
    registrado_por: int | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan ---
    asistio: bool | None = None
    observaciones: str | None = None
