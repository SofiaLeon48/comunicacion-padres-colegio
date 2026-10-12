from fastapi import APIRouter, Depends, Query

from app.core.deps import PERSONAL, requiere_roles
from app.repositories.reporte_repo import ReporteRepository

router = APIRouter(prefix="/reportes", tags=["Reportes y Analítica"],
                   dependencies=[Depends(requiere_roles(*PERSONAL))])
repo = ReporteRepository()


@router.get("/resumen", summary="Indicadores generales (tarjetas del dashboard)")
def resumen():
    return {**repo.resumen_general(),
            "usuarios_por_rol": repo.usuarios_por_rol(),
            "asistencia_citaciones": repo.asistencia_citaciones()}


@router.get("/lectura-comunicados", summary="% de lectura de cada comunicado")
def lectura_comunicados(curso_id: int | None = None):
    return repo.lectura_comunicados(curso_id)


@router.get("/acudientes-pendientes", summary="Acudientes con más comunicados sin confirmar")
def acudientes_pendientes(limite: int = Query(20, le=100)):
    return repo.acudientes_sin_leer(limite)


@router.get("/citaciones", summary="Citaciones por estado y % de asistencia")
def citaciones():
    return {"por_estado": repo.citaciones_por_estado(), "asistencia": repo.asistencia_citaciones()}


@router.get("/actividad-cursos", summary="Comunicados, mensajes y citaciones por curso")
def actividad_cursos():
    return repo.actividad_por_curso()


@router.get("/actividad-reciente", summary="Acciones por día (desde logs_actividad)")
def actividad_reciente(dias: int = Query(7, ge=1, le=90)):
    return repo.actividad_reciente(dias)
