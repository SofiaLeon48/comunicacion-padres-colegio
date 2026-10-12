from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.comun import Auditoria, Estado

Prioridad = Literal["normal", "urgente"]


class ComunicadoCrear(BaseModel):
    titulo: str = Field(min_length=3, max_length=150, examples=["Reunión de padres"])
    contenido: str = Field(min_length=1, examples=["Se cita a reunión general el viernes..."])
    curso_id: int | None = Field(default=None, description="Vacío = circular para todo el colegio")
    prioridad: Prioridad = "normal"
    requiere_confirmacion: bool = True


class ComunicadoActualizar(BaseModel):
    titulo: str | None = Field(default=None, min_length=3, max_length=150)
    contenido: str | None = Field(default=None, min_length=1)
    prioridad: Prioridad | None = None
    requiere_confirmacion: bool | None = None
    estado: Estado | None = None


class ComunicadoSalida(Auditoria):
    id: int
    titulo: str
    contenido: str
    curso_id: int | None
    curso_nombre: str | None = None
    autor_id: int
    autor_nombre: str | None = None
    prioridad: str
    requiere_confirmacion: bool
    fecha_publicacion: datetime
    confirmado_por_mi: bool | None = None


class ConfirmacionSalida(Auditoria):
    id: int
    comunicado_id: int
    usuario_id: int
    fecha_confirmacion: datetime


class EstadoLecturaItem(BaseModel):
    usuario_id: int
    nombre: str
    correo: str
    confirmado: bool
    fecha_confirmacion: datetime | None


class EstadoLectura(BaseModel):
    comunicado_id: int
    destinatarios: int
    confirmados: int
    porcentaje: float
    detalle: list[EstadoLecturaItem]
