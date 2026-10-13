from pydantic import BaseModel, Field

from app.models.comun import Auditoria, Estado


class ModuloCrear(BaseModel):
    clave: str = Field(min_length=3, max_length=30, pattern=r"^[a-z_]+$", examples=["eventos"])
    nombre: str = Field(min_length=3, max_length=50)
    descripcion: str | None = Field(default=None, max_length=150)
    ruta: str = Field(min_length=2, max_length=80, pattern=r"^/", examples=["/eventos"])
    icono: str = Field(default="bi-grid", max_length=40)
    orden: int = Field(default=0, ge=0, le=99)


class ModuloActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=50)
    descripcion: str | None = Field(default=None, max_length=150)
    ruta: str | None = Field(default=None, min_length=2, max_length=80, pattern=r"^/")
    icono: str | None = Field(default=None, max_length=40)
    orden: int | None = Field(default=None, ge=0, le=99)
    estado: Estado | None = None


class ModuloSalida(Auditoria):
    id: int
    clave: str
    nombre: str
    descripcion: str | None
    ruta: str
    icono: str
    orden: int


class PermisoItem(BaseModel):
    rol_id: int
    rol: str
    modulo_id: int
    clave: str
    modulo: str
    icono: str
    orden: int
    permitido: bool


class PermisoCambio(BaseModel):
    rol_id: int
    modulo_id: int
    permitido: bool
