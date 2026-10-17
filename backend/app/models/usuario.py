"""Tabla usuarios."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class Usuario(BaseModel):
    """Personas que usan la plataforma (coordinación, docentes y acudientes)."""
    # --- automáticos (los asigna la base de datos; se ignoran si llegan) ---
    id: int | None = None
    ultimo_acceso: datetime | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan ---
    nombre: str | None = Field(None, min_length=3, max_length=100, examples=["María Pérez"])
    correo: EmailStr | None = Field(None, examples=["maria.perez@correo.com"])
    password: str | None = Field(None, min_length=8, max_length=72, exclude=True,
                                 description="Solo se recibe; se guarda cifrada (password_hash) y nunca se devuelve")
    telefono: str | None = Field(None, max_length=20)
    rol_id: int | None = None
    # --- dato relacionado que trae la consulta (solo lectura) ---
    rol: str | None = None
