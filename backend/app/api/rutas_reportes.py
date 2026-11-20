"""
Módulo Reporte: consulta, exportación (PDF / Excel) y envío por correo.

Criterios de filtro (todos opcionales y combinables):
  - rango de fechas: desde / hasta
  - grupo
  - estado de la citación o prioridad del comunicado
"""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field

from app.core.deps import PERSONAL, UsuarioActual, requiere_modulo, requiere_roles
from app.repositories.reporte_repo import ReporteRepository
from app.services import ia, reportes
from app.services.correo import correo_habilitado, enviar_correo

router = APIRouter(prefix="/reportes", tags=["Reportes"],
                   dependencies=[Depends(requiere_roles(*PERSONAL)), Depends(requiere_modulo("reportes"))])
repo = ReporteRepository()
TipoReporte = Literal["comunicados", "citaciones"]
Formato = Literal["pdf", "excel"]
MIME = {"pdf": "application/pdf",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
EXT = {"pdf": "pdf", "excel": "xlsx"}


class Criterios(BaseModel):
    tipo: TipoReporte
    desde: date | None = None
    hasta: date | None = None
    grupo_id: int | None = None
    estado: str | None = None


class EnvioReporte(Criterios):
    formato: Formato = "pdf"
    correo: EmailStr
    mensaje: str | None = Field(None, max_length=500)
    incluir_analisis: bool = False


def criterios(tipo: TipoReporte, desde: date | None = None, hasta: date | None = None,
              grupo_id: int | None = None, estado: str | None = Query(None, description="Estado o prioridad")) -> Criterios:
    return Criterios(tipo=tipo, desde=desde, hasta=hasta, grupo_id=grupo_id, estado=estado or None)


def armar(c: Criterios) -> dict:
    return reportes.construir(c.tipo, c.desde, c.hasta, c.grupo_id, c.estado)


def generar_archivo(rep: dict, formato: str, usuario: dict, con_analisis: bool) -> tuple[str, bytes]:
    analisis = ia.analizar_reporte(rep["titulo"], reportes.texto_criterios(rep), rep["resumen"], rep["filas"]) \
        if con_analisis else None
    contenido = reportes.generar_pdf(rep, usuario["nombre"], analisis) if formato == "pdf" \
        else reportes.generar_excel(rep, usuario["nombre"], analisis)
    return reportes.nombre_archivo(rep, EXT[formato]), contenido


@router.get("/datos", summary="Vista previa del reporte con los criterios elegidos")
def datos(c: Criterios = Depends(criterios)):
    return armar(c)


@router.get("/exportar", summary="Descarga el reporte en PDF o Excel")
def exportar(usuario: UsuarioActual, formato: Formato, c: Criterios = Depends(criterios), analisis: bool = False):
    nombre, contenido = generar_archivo(armar(c), formato, usuario, analisis)
    return Response(contenido, media_type=MIME[formato],
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"',
                             "Access-Control-Expose-Headers": "Content-Disposition"})


@router.post("/enviar", summary="Envía el reporte por correo como archivo adjunto")
def enviar(datos: EnvioReporte, usuario: UsuarioActual):
    if not correo_habilitado():
        raise HTTPException(status_code=503, detail="El envío de correos no está configurado en el servidor.")
    rep = armar(datos)
    nombre, contenido = generar_archivo(rep, datos.formato, usuario, datos.incluir_analisis)
    nota = f"<p>{datos.mensaje}</p>" if datos.mensaje else ""
    html = f"""<div style="font-family:Segoe UI,Arial,sans-serif;color:#0f172a">
      <div style="background:#1E3A8A;color:#fff;padding:14px 18px;border-radius:8px 8px 0 0">
        <strong style="font-size:16px">Conecta Escolar</strong><br><span style="font-size:12px">{rep['titulo']}</span></div>
      <div style="border:1px solid #e2e8f0;border-top:0;padding:16px 18px;border-radius:0 0 8px 8px">
        <p>Hola,</p><p>{usuario['nombre']} te comparte el <b>{rep['titulo'].lower()}</b> en el archivo adjunto.</p>{nota}
        <p style="background:#E8EEFB;padding:8px 10px;border-radius:6px;font-size:13px">{reportes.texto_criterios(rep)}</p>
        <p style="font-size:13px">{' · '.join(f'<b>{k}:</b> {v}' for k, v in rep['resumen'].items())}</p>
        <p style="color:#64748b;font-size:12px">Mensaje automático de Conecta Escolar.</p></div></div>"""
    texto = f"{usuario['nombre']} te comparte el {rep['titulo'].lower()} ({reportes.texto_criterios(rep)})."
    if not enviar_correo([datos.correo], f"[Conecta Escolar] {rep['titulo']}", texto, html=html,
                         adjuntos=[(nombre, contenido)], copia_oculta=False):
        raise HTTPException(status_code=502, detail="No se pudo enviar el correo. Revisa la configuración del servicio de correo.")
    return {"mensaje": f"Reporte enviado a {datos.correo}.", "archivo": nombre}


@router.get("/analisis", summary="Conclusiones del reporte generadas con IA (Gemini)")
def analisis(c: Criterios = Depends(criterios)):
    rep = armar(c)
    return {"analisis": ia.analizar_reporte(rep["titulo"], reportes.texto_criterios(rep), rep["resumen"], rep["filas"])}


@router.get("/opciones", summary="Tipos de reporte, estados y servicios disponibles")
def opciones():
    return {
        "tipos": [{"valor": k, "titulo": v["titulo"], "estado_nombre": v["estado_nombre"], "estados": v["estados"]}
                  for k, v in reportes.TIPOS.items()],
        "correo_habilitado": correo_habilitado(),
        "ia_habilitada": ia.ia_habilitada(),
    }


# ---- Indicadores usados por Inicio y por las pruebas (se conservan) ----
@router.get("/resumen", summary="Indicadores generales")
def resumen():
    return {**repo.resumen_general(),
            "usuarios_por_rol": repo.usuarios_por_rol(),
            "asistencia_citaciones": repo.asistencia_citaciones()}


@router.get("/lectura-comunicados", summary="% de lectura de cada comunicado")
def lectura_comunicados(grupo_id: int | None = None):
    return repo.lectura_comunicados(grupo_id)


@router.get("/acudientes-pendientes", summary="Acudientes con más comunicados sin confirmar")
def acudientes_pendientes(limite: int = Query(20, le=100)):
    return repo.acudientes_sin_leer(limite)


@router.get("/citaciones", summary="Citaciones por estado y % de asistencia")
def citaciones():
    return {"por_estado": repo.citaciones_por_estado(), "asistencia": repo.asistencia_citaciones()}


@router.get("/actividad-grupos", summary="Comunicados, mensajes y citaciones por grupo")
def actividad_grupos():
    return repo.actividad_por_grupo()
