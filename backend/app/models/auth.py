from pydantic import BaseModel, EmailStr, Field

from app.models.usuario import UsuarioSalida


class LoginEntrada(BaseModel):
    correo: EmailStr = Field(examples=["coordinacion@colegio.edu.co"])
    password: str = Field(examples=["Colegio2026*"])
    rol: str = Field(description="Rol con el que se ingresa (debe coincidir con el del usuario)",
                     examples=["coordinacion"])


class ModuloMenu(BaseModel):
    clave: str
    nombre: str
    descripcion: str | None
    ruta: str
    icono: str
    orden: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioSalida
    modulos: list[ModuloMenu] = []


class RolPublico(BaseModel):
    nombre: str
    descripcion: str | None
