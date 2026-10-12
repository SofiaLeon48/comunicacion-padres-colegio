from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.comun import Auditoria


class MensajeCrear(BaseModel):
    curso_id: int | None = Field(default=None, description="Para el chat del curso")
    destinatario_id: int | None = Field(default=None, description="Para un mensaje directo")
    contenido: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def un_solo_destino(self):
        if (self.curso_id is None) == (self.destinatario_id is None):
            raise ValueError("Indica curso_id (chat del curso) o destinatario_id (directo), solo uno.")
        return self


class MensajeEditar(BaseModel):
    contenido: str = Field(min_length=1, max_length=2000)


class MensajeSalida(Auditoria):
    id: int
    remitente_id: int
    remitente_nombre: str | None = None
    remitente_rol: str | None = None
    curso_id: int | None
    destinatario_id: int | None
    contenido: str
    leido: bool
    fecha_envio: datetime


class Conversacion(BaseModel):
    contraparte_id: int
    contraparte_nombre: str
    contraparte_rol: str
    ultimo_mensaje: str
    fecha_envio: datetime
    no_leidos: int
