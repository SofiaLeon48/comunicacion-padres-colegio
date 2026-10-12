"""
Carga datos de demostración (usuarios de prueba, cursos, estudiantes, etc.).

    python -m scripts.seed

Todos los usuarios de prueba tienen la contraseña:  Colegio2026*
"""
from datetime import timedelta

from app.core.config import ahora_local, settings
from app.core.security import hashear_password
from app.repositories.acudiente_estudiante_repo import AcudienteEstudianteRepository
from app.repositories.citacion_repo import CitacionRepository
from app.repositories.comunicado_repo import ComunicadoRepository
from app.repositories.curso_repo import CursoRepository
from app.repositories.estudiante_repo import EstudianteRepository
from app.repositories.mensaje_repo import MensajeRepository
from app.repositories.rol_repo import RolRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services.notificador import notificar

PASSWORD_DEMO = "Colegio2026*"

USUARIOS = [
    # (clave, nombre, correo, rol, teléfono)
    ("admin",   "Administrador General", "admin@colegio.edu.co",        "admin",        None),
    ("coord",   "Patricia Herrera",      "coordinacion@colegio.edu.co", "coordinacion", "3001112233"),
    ("doc1",    "Luis Martínez",         "lmartinez@colegio.edu.co",    "docente",      "3002223344"),
    ("doc2",    "Carolina Gómez",        "cgomez@colegio.edu.co",       "docente",      "3003334455"),
    ("acu1",    "María Rodríguez",       "maria.rodriguez@correo.com",  "acudiente",    "3101234567"),
    ("acu2",    "Jorge Pérez",           "jorge.perez@correo.com",      "acudiente",    "3112345678"),
    ("acu3",    "Ana Sánchez",           "ana.sanchez@correo.com",      "acudiente",    "3123456789"),
    ("acu4",    "Laura Díaz",            "laura.diaz@correo.com",       "acudiente",    "3134567890"),
]


def sembrar() -> dict:
    roles = {r["nombre"]: r["id"] for r in RolRepository().listar()}
    usuarios_repo = UsuarioRepository()
    hash_demo = hashear_password(PASSWORD_DEMO)

    u = {}
    for clave, nombre, correo, rol, tel in USUARIOS:
        existente = usuarios_repo.obtener_por_correo(correo)
        u[clave] = existente or usuarios_repo.crear({
            "nombre": nombre, "correo": correo, "password_hash": hash_demo,
            "telefono": tel, "rol_id": roles[rol]})

    cursos_repo = CursoRepository()
    c5a = cursos_repo.crear({"nombre": "5A", "grado": 5, "jornada": "manana", "director_id": u["doc1"]["id"]})
    c6b = cursos_repo.crear({"nombre": "6B", "grado": 6, "jornada": "tarde", "director_id": u["doc2"]["id"]})

    est_repo = EstudianteRepository()
    e = {
        "santiago": est_repo.crear({"nombre": "Santiago Rodríguez", "documento": "1043000001", "curso_id": c5a["id"]}),
        "valentina": est_repo.crear({"nombre": "Valentina Rodríguez", "documento": "1043000002", "curso_id": c6b["id"]}),
        "samuel": est_repo.crear({"nombre": "Samuel Pérez Díaz", "documento": "1043000003", "curso_id": c5a["id"]}),
        "isabella": est_repo.crear({"nombre": "Isabella Sánchez", "documento": "1043000004", "curso_id": c6b["id"]}),
        "mateo": est_repo.crear({"nombre": "Mateo Castro", "documento": "1043000005", "curso_id": c5a["id"]}),
    }

    vinc = AcudienteEstudianteRepository()
    for acu, est, parentesco, principal in [
        ("acu1", "santiago", "madre", True), ("acu1", "valentina", "madre", True),
        ("acu2", "samuel", "padre", True), ("acu4", "samuel", "madre", False),
        ("acu3", "isabella", "madre", True),
    ]:
        vinc.crear({"acudiente_id": u[acu]["id"], "estudiante_id": e[est]["id"],
                    "parentesco": parentesco, "es_principal": principal})

    com_repo = ComunicadoRepository()
    general = com_repo.crear({
        "titulo": "Bienvenida al nuevo canal oficial", "autor_id": u["coord"]["id"], "curso_id": None,
        "contenido": "A partir de hoy todas las circulares del colegio llegarán por esta plataforma. "
                     "Por favor confirma la lectura de cada comunicado.",
        "prioridad": "normal", "requiere_confirmacion": True})
    salida = com_repo.crear({
        "titulo": "Salida pedagógica al Museo del Caribe", "autor_id": u["doc1"]["id"], "curso_id": c5a["id"],
        "contenido": "El próximo viernes realizaremos la salida pedagógica. Traer uniforme de educación física "
                     "y autorización firmada.", "prioridad": "urgente", "requiere_confirmacion": True})
    for com in (general, salida):
        dest = [d["id"] for d in com_repo.destinatarios(com["curso_id"])]
        notificar(dest, "comunicado", com["titulo"], com["contenido"][:250], com["id"])

    msg = MensajeRepository()
    msg.crear({"remitente_id": u["doc1"]["id"], "curso_id": c5a["id"],
               "contenido": "¡Bienvenidos al chat del 5A! Aquí resolveremos dudas del curso."})
    msg.crear({"remitente_id": u["acu2"]["id"], "curso_id": c5a["id"],
               "contenido": "Gracias profe. ¿La salida del viernes tiene algún costo?"})
    msg.crear({"remitente_id": u["acu1"]["id"], "destinatario_id": u["doc2"]["id"],
               "contenido": "Buenas tardes profesora, Valentina estuvo enferma ayer. Adjuntaré la excusa."})

    cit = CitacionRepository().crear({
        "estudiante_id": e["samuel"]["id"], "docente_id": u["doc1"]["id"],
        "motivo": "Seguimiento académico del primer periodo",
        "fecha_hora": (ahora_local() + timedelta(days=3)).replace(hour=7, minute=30, second=0, microsecond=0),
        "lugar": "Sala de profesores"})
    notificar([u["acu2"]["id"], u["acu4"]["id"]], "citacion", "Citación: Samuel Pérez Díaz",
              cit["motivo"], cit["id"])

    return {"usuarios": u, "cursos": {"5A": c5a, "6B": c6b}, "estudiantes": e,
            "comunicados": {"general": general, "salida": salida}, "citacion": cit}


if __name__ == "__main__":
    if not settings.DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el archivo .env")
    sembrar()
    print("✔ Datos de demostración cargados.\n")
    print(f"Usuarios de prueba (contraseña: {PASSWORD_DEMO}):")
    for _, nombre, correo, rol, _ in USUARIOS:
        print(f"  {rol:<13} {correo:<32} {nombre}")
