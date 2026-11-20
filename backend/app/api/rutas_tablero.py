"""
Módulo Tablero (dashboard).

El tablero se PUBLICA como una página web propia de la API (/tablero/publico) y se
COMPARTE mediante un <iframe> dentro del módulo Tablero de la aplicación.
La página pública no pide inicio de sesión: la protege una llave (t=...) que solo
entrega la API a usuarios con permiso sobre el módulo.
"""
import hashlib
import hmac
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.deps import PERSONAL, requiere_modulo, requiere_roles
from app.repositories.tablero_repo import TableroRepository

router = APIRouter(prefix="/tablero", tags=["Tablero (dashboard)"])
repo = TableroRepository()
PAGINA = Path(__file__).resolve().parent.parent / "static" / "tablero.html"


def llave_tablero() -> str:
    if settings.TABLERO_TOKEN:
        return settings.TABLERO_TOKEN
    return hmac.new(settings.JWT_SECRET.encode(), b"tablero-publicado", hashlib.sha256).hexdigest()[:32]


def verificar_llave(t: str = Query(..., description="Llave del enlace publicado")) -> None:
    if not hmac.compare_digest(t, llave_tablero()):
        raise HTTPException(status_code=403, detail="Enlace del tablero inválido.")


def validar_rango(desde: date | None, hasta: date | None) -> None:
    if desde and hasta and desde > hasta:
        raise HTTPException(status_code=422, detail="La fecha inicial no puede ser posterior a la final.")


@router.get("/enlace", summary="Enlace publicado del tablero (para el iframe)",
            dependencies=[Depends(requiere_roles(*PERSONAL)), Depends(requiere_modulo("tablero"))])
def enlace():
    t = llave_tablero()
    return {"ruta": f"/tablero/publico?t={t}", "llave": t}


@router.get("/publico", response_class=HTMLResponse, summary="Tablero publicado (página para el iframe)",
            dependencies=[Depends(verificar_llave)])
def pagina_publica():
    return HTMLResponse(PAGINA.read_text(encoding="utf-8"))


@router.get("/publico/datos", summary="Indicadores y datos de los gráficos del tablero",
            dependencies=[Depends(verificar_llave)])
def datos(grupo_id: int | None = None, desde: date | None = None, hasta: date | None = None):
    validar_rango(desde, hasta)
    return repo.todo(grupo_id, desde, hasta)


@router.get("/publico/grupos", summary="Grupos para el filtro del tablero", dependencies=[Depends(verificar_llave)])
def grupos():
    return repo.grupos()
