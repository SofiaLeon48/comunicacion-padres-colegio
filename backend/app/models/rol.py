from pydantic import BaseModel, Field

from app.models.comun import Auditoria, Estado


class RolCrear(BaseModel):
    nombre: str = Field(min_length=3, max_length=30, examples=["docente"])
    descripcion: str | None = Field(default=None, max_length=150)


class RolActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=30)
    descripcion: str | None = Field(default=None, max_length=150)
    estado: Estado | None = None


class RolSalida(Auditoria):
    id: int
    nombre: str
    descripcion: str | None
