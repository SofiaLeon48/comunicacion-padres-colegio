from typing import Literal

from pydantic import BaseModel, Field

from app.models.comun import Auditoria, Estado

Jornada = Literal["manana", "tarde", "unica"]


class CursoCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=20, examples=["5A"])
    grado: int = Field(ge=0, le=11, examples=[5])
    jornada: Jornada = "manana"
    anio_lectivo: int | None = Field(default=None, ge=2000, le=2100)
    director_id: int | None = None


class CursoActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=20)
    grado: int | None = Field(default=None, ge=0, le=11)
    jornada: Jornada | None = None
    anio_lectivo: int | None = Field(default=None, ge=2000, le=2100)
    director_id: int | None = None
    estado: Estado | None = None


class CursoSalida(Auditoria):
    id: int
    nombre: str
    grado: int
    jornada: str
    anio_lectivo: int
    director_id: int | None
    director_nombre: str | None = None
    total_estudiantes: int | None = None
