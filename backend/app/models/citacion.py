from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.config import a_hora_local

from app.models.comun import Auditoria, Estado

EstadoCitacion = Literal["pendiente", "confirmada", "cancelada", "realizada"]


class CitacionCrear(BaseModel):
    estudiante_id: int
    acudiente_id: int | None = Field(default=None, description="Vacío = todos los acudientes del estudiante")
    motivo: str = Field(min_length=3, max_length=255, examples=["Seguimiento académico"])
    fecha_hora: datetime = Field(examples=["2026-10-20T07:30:00"])
    lugar: str | None = Field(default=None, max_length=100, examples=["Sala de profesores"])
    docente_id: int | None = Field(default=None, description="Solo admin/coordinación: citar a nombre de otro docente")

    @field_validator("fecha_hora")
    @classmethod
    def _hora_local(cls, v):
        return a_hora_local(v)


class CitacionActualizar(BaseModel):
    motivo: str | None = Field(default=None, min_length=3, max_length=255)
    fecha_hora: datetime | None = None
    lugar: str | None = Field(default=None, max_length=100)
    acudiente_id: int | None = None
    estado: Estado | None = None

    @field_validator("fecha_hora")
    @classmethod
    def _hora_local(cls, v):
        return a_hora_local(v)


class CambioEstadoCitacion(BaseModel):
    estado_citacion: EstadoCitacion


class CitacionSalida(Auditoria):
    id: int
    estudiante_id: int
    estudiante_nombre: str | None = None
    curso_nombre: str | None = None
    docente_id: int
    docente_nombre: str | None = None
    acudiente_id: int | None
    acudiente_nombre: str | None = None
    motivo: str
    fecha_hora: datetime
    lugar: str | None
    estado_citacion: str
    asistio: bool | None = None
    observaciones: str | None = None


class AsistenciaCrear(BaseModel):
    asistio: bool
    observaciones: str | None = None


class AsistenciaActualizar(BaseModel):
    asistio: bool | None = None
    observaciones: str | None = None


class AsistenciaSalida(Auditoria):
    id: int
    citacion_id: int
    asistio: bool
    observaciones: str | None
    registrado_por: int
