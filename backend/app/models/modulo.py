"""Tabla modulos."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Modulo(BaseModel):
    """Secciones de la aplicación: cada una es una opción del menú."""
    # --- automáticos (los asigna la base de datos; se ignoran si llegan) ---
    id: int | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan ---
    clave: str | None = Field(None, min_length=3, max_length=30, pattern=r"^[a-z_]+$", examples=["eventos"])
    nombre: str | None = Field(None, min_length=3, max_length=50)
    descripcion: str | None = Field(None, max_length=150)
    ruta: str | None = Field(None, min_length=2, max_length=80, pattern=r"^/", examples=["/eventos"])
    icono: str | None = Field(None, max_length=40, examples=["bi-grid"])
    orden: int | None = Field(None, ge=0, le=99)
