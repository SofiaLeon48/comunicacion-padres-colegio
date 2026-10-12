from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.comun import Auditoria, Estado, NombreRol


class UsuarioCrear(BaseModel):
    nombre: str = Field(min_length=3, max_length=100, examples=["María Pérez"])
    correo: EmailStr = Field(examples=["maria.perez@correo.com"])
    password: str = Field(min_length=8, max_length=72, description="Se guarda cifrada con bcrypt")
    telefono: str | None = Field(default=None, max_length=20)
    rol_id: int


class UsuarioActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=100)
    correo: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    telefono: str | None = Field(default=None, max_length=20)
    rol_id: int | None = None
    estado: Estado | None = None


class PerfilActualizar(BaseModel):
    """Lo que un usuario puede cambiar de sí mismo."""
    nombre: str | None = Field(default=None, min_length=3, max_length=100)
    telefono: str | None = Field(default=None, max_length=20)


class CambioPassword(BaseModel):
    password_actual: str
    password_nueva: str = Field(min_length=8, max_length=72)


class UsuarioSalida(Auditoria):
    """Nunca incluye password_hash."""
    id: int
    nombre: str
    correo: str
    telefono: str | None
    rol_id: int
    rol: NombreRol | str | None = None
    ultimo_acceso: datetime | None = None
