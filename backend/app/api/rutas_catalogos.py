"""
Catálogos para las listas desplegables del frontend.

El frontend NUNCA pide al usuario escribir un ID: muestra nombres en un <select>
y por debajo envía el id seleccionado. Estos endpoints devuelven solo lo
necesario para esas listas, filtrado según el rol de quien pregunta.
"""
from fastapi import APIRouter

from app.core.deps import UsuarioActual, es_personal, prohibido
from app.repositories.base import BaseRepository

router = APIRouter(prefix="/catalogos", tags=["Catálogos (listas desplegables)"])
db = BaseRepository()

JORNADAS = {"manana": "Mañana", "tarde": "Tarde", "unica": "Única"}


@router.get("/grupos")
def grupos(usuario: UsuarioActual):
    filtro, valores = "", []
    if usuario["rol"] == "acudiente":
        filtro = """AND c.id IN (SELECT e.grupo_id FROM estudiantes e
                    JOIN acudiente_estudiante ae ON ae.estudiante_id = e.id
                    WHERE ae.acudiente_id = %s AND ae.estado = 'activo' AND e.estado = 'activo')"""
        valores = [usuario["id"]]
    filas = db._todos(f"""SELECT c.id, c.nombre, c.grado, c.jornada, c.director_id FROM grupos c
                          WHERE c.estado = 'activo' {filtro} ORDER BY c.grado, c.nombre""", valores)
    return [{**f, "etiqueta": f"{f['nombre']} · Jornada {JORNADAS.get(f['jornada'], f['jornada'])}"} for f in filas]


@router.get("/estudiantes")
def estudiantes(usuario: UsuarioActual, grupo_id: int | None = None):
    condiciones, valores = ["e.estado = 'activo'"], []
    if grupo_id:
        condiciones.append("e.grupo_id = %s")
        valores.append(grupo_id)
    if usuario["rol"] == "acudiente":
        condiciones.append("""e.id IN (SELECT estudiante_id FROM acudiente_estudiante
                              WHERE acudiente_id = %s AND estado = 'activo')""")
        valores.append(usuario["id"])
    filas = db._todos(f"""SELECT e.id, e.nombre, c.nombre AS grupo FROM estudiantes e
                          JOIN grupos c ON c.id = e.grupo_id
                          WHERE {" AND ".join(condiciones)} ORDER BY e.nombre""", valores)
    return [{**f, "etiqueta": f"{f['nombre']} ({f['grupo']})"} for f in filas]


@router.get("/acudientes")
def acudientes(usuario: UsuarioActual, estudiante_id: int | None = None):
    if not es_personal(usuario):
        raise prohibido()
    if estudiante_id:
        filas = db._todos("""SELECT u.id, u.nombre, ae.parentesco FROM acudiente_estudiante ae
                             JOIN usuarios u ON u.id = ae.acudiente_id
                             WHERE ae.estudiante_id = %s AND ae.estado = 'activo' AND u.estado = 'activo'
                             ORDER BY ae.es_principal DESC, u.nombre""", (estudiante_id,))
        return [{**f, "etiqueta": f"{f['nombre']} ({f['parentesco']})"} for f in filas]
    filas = db._todos("""SELECT u.id, u.nombre, u.correo FROM usuarios u JOIN roles r ON r.id = u.rol_id
                         WHERE r.nombre = 'acudiente' AND u.estado = 'activo' ORDER BY u.nombre""")
    return [{**f, "etiqueta": f"{f['nombre']} — {f['correo']}"} for f in filas]


@router.get("/docentes")
def docentes(usuario: UsuarioActual):
    filas = db._todos("""SELECT u.id, u.nombre, r.nombre AS rol FROM usuarios u JOIN roles r ON r.id = u.rol_id
                         WHERE r.nombre IN ('docente', 'coordinacion') AND u.estado = 'activo'
                         ORDER BY r.nombre DESC, u.nombre""")
    return [{**f, "etiqueta": f["nombre"] + (" (Coordinación)" if f["rol"] == "coordinacion" else "")}
            for f in filas]


@router.get("/contactos", summary="Personas a las que puedo escribir un mensaje directo")
def contactos(usuario: UsuarioActual):
    if usuario["rol"] == "acudiente":
        filtro = "r.nombre IN ('docente', 'coordinacion')"
    else:
        filtro = "TRUE"
    filas = db._todos(f"""SELECT u.id, u.nombre, r.nombre AS rol FROM usuarios u JOIN roles r ON r.id = u.rol_id
                          WHERE u.estado = 'activo' AND u.id <> %s AND {filtro}
                          ORDER BY r.nombre, u.nombre""", (usuario["id"],))
    nombres = {"coordinacion": "Coordinación", "docente": "Docente", "acudiente": "Acudiente"}
    return [{**f, "etiqueta": f"{f['nombre']} · {nombres.get(f['rol'], f['rol'])}"} for f in filas]


@router.get("/roles")
def roles(_: UsuarioActual):
    nombres = {"coordinacion": "Coordinación", "docente": "Docente", "acudiente": "Acudiente"}
    filas = db._todos("SELECT id, nombre FROM roles WHERE estado = 'activo' ORDER BY id")
    return [{**f, "etiqueta": nombres.get(f["nombre"], f["nombre"].capitalize())} for f in filas]
