"""Tipos compartidos por todos los modelos."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Estado = Literal["activo", "inactivo"]
NombreRol = Literal["admin", "coordinacion", "docente", "acudiente"]


class Auditoria(BaseModel):
    """Campos de auditoría presentes en las 12 tablas (solo lectura)."""
    model_config = ConfigDict(from_attributes=True)
    creado: datetime
    modificado: datetime
    estado: Estado


class Mensaje(BaseModel):
    mensaje: str
