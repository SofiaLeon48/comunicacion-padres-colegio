"""
API de Comunicación Padres-Colegio en Tiempo Real.

Ejecutar:   uvicorn main:app --reload
Documentación interactiva:  http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (rutas_acudiente_estudiante, rutas_auth, rutas_catalogos, rutas_citacion,
                     rutas_comunicado, rutas_configuracion, rutas_grupo, rutas_estudiante,
                     rutas_inicio, rutas_mensaje, rutas_notificacion,
                     rutas_reportes, rutas_rol, rutas_tiempo_real, rutas_usuario)
from app.core.config import settings
from app.core.database import cerrar_pool, get_cursor
from app.core.errores import registrar_manejadores


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    yield
    cerrar_pool()   # al apagar el servidor se cierran las conexiones a Neon


app = FastAPI(
    title="API de Comunicación Padres-Colegio",
    description=(
        "Plataforma oficial de comunicación entre el colegio y los acudientes: circulares digitales "
        "con confirmación de lectura, mensajería por grupo y directa, calendario de citaciones, "
        "notificaciones en tiempo real y reportes.\n\n"
        "**Cómo probar:** clic en **Authorize** e inicia sesión con un usuario de prueba "
        "(ver README)."
    ),
    version="4.0.0",
    lifespan=ciclo_de_vida,
)

# CORS: permite que el frontend (Svelte, en otro puerto/dominio) consuma la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_manejadores(app)

# Módulo: Usuarios y Roles
app.include_router(rutas_auth.router)
app.include_router(rutas_usuario.router)
app.include_router(rutas_inicio.router)
app.include_router(rutas_catalogos.router)
# Módulo: Administración
app.include_router(rutas_grupo.router)
app.include_router(rutas_estudiante.router)
app.include_router(rutas_acudiente_estudiante.router)
# Módulo: Comunicados y Mensajería (principal)
app.include_router(rutas_comunicado.router)
app.include_router(rutas_mensaje.router)
app.include_router(rutas_citacion.router)
# Módulo: Notificaciones
app.include_router(rutas_notificacion.router)
app.include_router(rutas_tiempo_real.router)
# Módulo: Reportes y Analítica
app.include_router(rutas_reportes.router)
# Módulo: Configuración (roles, módulos y permisos rol x módulo)
app.include_router(rutas_rol.router)
app.include_router(rutas_configuracion.router)


@app.get("/", tags=["Estado"])
def estado_api():
    return {"mensaje": "API de comunicación padres-colegio en línea", "docs": "/docs"}


@app.get("/salud", tags=["Estado"], summary="Verifica la conexión con la base de datos")
def salud():
    with get_cursor() as cur:
        cur.execute("SELECT NOW() AS hora_bd, current_setting('TimeZone') AS zona")
        return {"api": "ok", "base_de_datos": "ok", **cur.fetchone()}
