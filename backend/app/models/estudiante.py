from pydantic import BaseModel, Field

from app.models.comun import Auditoria, Estado


class EstudianteCrear(BaseModel):
    nombre: str = Field(min_length=3, max_length=100, examples=["Juan Pérez"])
    documento: str = Field(min_length=4, max_length=20, examples=["1043000111"])
    curso_id: int


class EstudianteActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=100)
    documento: str | None = Field(default=None, min_length=4, max_length=20)
    curso_id: int | None = None
    estado: Estado | None = None


class EstudianteSalida(Auditoria):
    id: int
    nombre: str
    documento: str
    curso_id: int
    curso_nombre: str | None = None
    curso_jornada: str | None = None
    director_nombre: str | None = None
    acudientes: str | None = None


class AcudienteDeEstudiante(BaseModel):
    id: int
    nombre: str
    correo: str
    telefono: str | None
    parentesco: str
    es_principal: bool
