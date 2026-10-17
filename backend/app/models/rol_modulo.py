"""Tabla rol_modulo."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class RolModulo(BaseModel):
    """Qué módulos (opciones del menú) tiene cada rol."""
    # --- automáticos (los asigna la base de datos; se ignoran si llegan) ---
    id: int | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
    # --- atributos que se llenan ---
    rol_id: int | None = None
    modulo_id: int | None = None
    # --- datos de la matriz de permisos (solo lectura, salvo 'permitido') ---
    permitido: bool | None = None
    rol: str | None = None
    clave: str | None = None
    modulo: str | None = None
    icono: str | None = None
    orden: int | None = None
