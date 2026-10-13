from fastapi import APIRouter, Depends

from app.core.config import ahora_local
from app.core.deps import UsuarioActual, requiere_modulo
from app.repositories.base import BaseRepository
from app.repositories.citacion_repo import CitacionRepository
from app.repositories.comunicado_repo import ComunicadoRepository
from app.repositories.estudiante_repo import EstudianteRepository
from app.repositories.notificacion_repo import NotificacionRepository
from app.repositories.reporte_repo import ReporteRepository

router = APIRouter(prefix="/inicio", tags=["Inicio"], dependencies=[Depends(requiere_modulo("inicio"))])
db = BaseRepository()
comunicados = ComunicadoRepository()
citaciones = CitacionRepository()
notificaciones = NotificacionRepository()
estudiantes = EstudianteRepository()
reportes = ReporteRepository()


@router.get("/resumen", summary="Datos del tablero de inicio según el rol")
def resumen(usuario: UsuarioActual):
    rol, uid = usuario["rol"], usuario["id"]
    visibles = comunicados.listar_visibles(uid, rol == "acudiente")
    proximas = [c for c in citaciones.listar_detallado(
        desde=ahora_local(),
        docente_id=uid if rol == "docente" else None,
        acudiente_id=uid if rol == "acudiente" else None)
        if c["estado_citacion"] in ("pendiente", "confirmada")]
    datos = {
        "rol": rol,
        "notificaciones_no_leidas": notificaciones.contar_no_leidas(uid),
        "ultimos_comunicados": visibles[:5],
        "proximas_citaciones": proximas[:5],
        "total_citaciones_proximas": len(proximas),
    }
    mensajes_no_leidos = db._uno("""SELECT COUNT(*) AS n FROM mensajes
                                    WHERE destinatario_id = %s AND NOT leido AND estado = 'activo'""", (uid,))["n"]
    datos["mensajes_no_leidos"] = mensajes_no_leidos

    if rol == "acudiente":
        datos["hijos"] = estudiantes.listar_detallado(acudiente_id=uid)
        datos["comunicados_pendientes"] = sum(
            1 for c in visibles if c["requiere_confirmacion"] and not c["confirmado_por_mi"])
    elif rol == "docente":
        propios = db._uno("""SELECT COUNT(*) AS n FROM comunicados WHERE autor_id = %s AND estado = 'activo'""",
                          (uid,))["n"]
        datos["mis_cursos"] = db._todos("""
            SELECT c.nombre, c.jornada,
                   (SELECT COUNT(*) FROM estudiantes e WHERE e.curso_id = c.id AND e.estado = 'activo') AS estudiantes
            FROM cursos c WHERE c.director_id = %s AND c.estado = 'activo' ORDER BY c.grado""", (uid,))
        datos["comunicados_publicados"] = propios
        lectura = [x for x in reportes.lectura_comunicados()
                   if any(c["id"] == x["id"] and c["autor_id"] == uid for c in visibles)]
        datos["lectura_promedio"] = round(sum(float(x["porcentaje_lectura"]) for x in lectura) / len(lectura), 1) \
            if lectura else 0
    else:
        datos["indicadores"] = reportes.resumen_general()
        lectura = reportes.lectura_comunicados()
        datos["lectura_promedio"] = round(sum(float(x["porcentaje_lectura"]) for x in lectura) / len(lectura), 1) \
            if lectura else 0
        datos["lectura_comunicados"] = lectura[:6]
        datos["usuarios_por_rol"] = reportes.usuarios_por_rol()
    return datos
