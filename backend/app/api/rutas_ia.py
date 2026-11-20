"""Funciones de inteligencia artificial (Google Gemini) para el personal del colegio."""
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import PERSONAL, requiere_roles
from app.services import ia

router = APIRouter(prefix="/ia", tags=["Inteligencia artificial"], dependencies=[Depends(requiere_roles(*PERSONAL))])


class IdeaComunicado(BaseModel):
    idea: str = Field(..., min_length=10, max_length=600, description="Qué se quiere comunicar")
    tono: Literal["formal", "cercano", "urgente"] = "formal"
    destinatarios: str = Field("todos los acudientes", max_length=80)


@router.get("/estado", summary="¿Está configurada la IA?")
def estado():
    return {"habilitada": ia.ia_habilitada()}


@router.post("/redactar-comunicado", summary="Redacta título y contenido de una circular a partir de una idea")
def redactar(datos: IdeaComunicado):
    return ia.redactar_comunicado(datos.idea, datos.tono, datos.destinatarios)
