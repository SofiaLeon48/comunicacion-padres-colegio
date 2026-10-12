"""
Manejo centralizado de errores de base de datos.

En lugar de repetir try/except en cada endpoint, se registran manejadores
globales: cualquier violación de integridad que lance PostgreSQL se traduce
a una respuesta HTTP clara (400/404/409/503) en vez de un 500 genérico.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from psycopg2 import OperationalError, errors as pg

from app.core.database import BaseDeDatosNoDisponible

# Mensajes amigables según el nombre de la restricción violada
MENSAJES_RESTRICCION = {
    "uq_usuarios_correo": "Ya existe un usuario con ese correo.",
    "roles_nombre_key": "Ya existe un rol con ese nombre.",
    "uq_cursos_nombre_jornada_anio": "Ya existe un curso con ese nombre, jornada y año lectivo.",
    "uq_estudiantes_documento": "Ya existe un estudiante con ese documento.",
    "uq_acudiente_estudiante": "Ese acudiente ya está vinculado a ese estudiante.",
    "uq_confirmacion_por_usuario": "Ya confirmaste la lectura de este comunicado.",
    "uq_asistencia_por_citacion": "Esta citación ya tiene asistencia registrada.",
    "ck_mensajes_destino": "Un mensaje debe ir a un curso o a un destinatario (solo uno de los dos).",
    "ck_mensajes_no_a_si_mismo": "No puedes enviarte un mensaje a ti mismo.",
    "ck_cursos_jornada": "Jornada inválida. Usa: manana, tarde o unica.",
    "ck_cursos_grado": "El grado debe estar entre 0 (transición) y 11.",
    "ck_comunicados_prioridad": "Prioridad inválida. Usa: normal o urgente.",
    "ck_citaciones_estado_citacion": "Estado de citación inválido.",
    "ck_notificaciones_tipo": "Tipo de notificación inválido.",
}


def _respuesta(status: int, detalle: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detalle})


def registrar_manejadores(app: FastAPI) -> None:

    @app.exception_handler(pg.UniqueViolation)
    async def unico(_: Request, e: pg.UniqueViolation):
        nombre = e.diag.constraint_name or ""
        return _respuesta(409, MENSAJES_RESTRICCION.get(nombre, "Ya existe un registro con ese valor único."))

    @app.exception_handler(pg.ForeignKeyViolation)
    async def llave_foranea(_: Request, e: pg.ForeignKeyViolation):
        return _respuesta(400, "Alguno de los ID referenciados no existe (revisa los campos *_id).")

    @app.exception_handler(pg.CheckViolation)
    async def check(_: Request, e: pg.CheckViolation):
        nombre = e.diag.constraint_name or ""
        return _respuesta(400, MENSAJES_RESTRICCION.get(nombre, f"Valor no permitido ({nombre})."))

    @app.exception_handler(pg.NotNullViolation)
    async def no_nulo(_: Request, e: pg.NotNullViolation):
        return _respuesta(400, f"El campo '{e.diag.column_name}' es obligatorio.")

    @app.exception_handler(pg.InvalidTextRepresentation)
    async def formato(_: Request, e: pg.InvalidTextRepresentation):
        return _respuesta(400, "Formato de dato inválido.")

    @app.exception_handler(BaseDeDatosNoDisponible)
    async def bd_caida(_: Request, e: BaseDeDatosNoDisponible):
        return _respuesta(503, "La base de datos no está disponible en este momento.")

    @app.exception_handler(OperationalError)
    async def operacional(_: Request, e: OperationalError):
        return _respuesta(503, "Se perdió la conexión con la base de datos. Intenta de nuevo.")
