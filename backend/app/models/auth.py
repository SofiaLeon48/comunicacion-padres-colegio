from pydantic import BaseModel

from app.models.usuario import UsuarioSalida


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioSalida
