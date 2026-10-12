from pydantic import BaseModel, Field

from app.models.comun import Auditoria, Estado


class VinculoCrear(BaseModel):
    acudiente_id: int
    estudiante_id: int
    parentesco: str = Field(default="acudiente", max_length=30, examples=["madre"])
    es_principal: bool = False


class VinculoActualizar(BaseModel):
    parentesco: str | None = Field(default=None, max_length=30)
    es_principal: bool | None = None
    estado: Estado | None = None


class VinculoSalida(Auditoria):
    id: int
    acudiente_id: int
    estudiante_id: int
    parentesco: str
    es_principal: bool
    acudiente_nombre: str | None = None
    estudiante_nombre: str | None = None
    curso_nombre: str | None = None
