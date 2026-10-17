"""Tabla confirmaciones_lectura."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ConfirmacionLectura(BaseModel):
    """Registro de que un acudiente leyó un comunicado (todo lo pone la API)."""
    id: int | None = None
    comunicado_id: int | None = None
    usuario_id: int | None = None
    fecha_confirmacion: datetime | None = None
    creado: datetime | None = None
    modificado: datetime | None = None
    estado: Literal["activo", "inactivo"] | None = None
