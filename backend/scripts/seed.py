"""
Carga datos de demostración realistas: usuarios, cursos, estudiantes, circulares,
mensajes, citaciones y notificaciones de un colegio de Barranquilla.

    python -m scripts.seed

Todos los usuarios de prueba tienen la contraseña:  Colegio2026*
"""
import random
from datetime import timedelta

from app.core.config import ahora_local, settings
from app.core.database import get_cursor
from app.core.security import hashear_password
from app.repositories.acudiente_estudiante_repo import AcudienteEstudianteRepository
from app.repositories.asistencia_citacion_repo import AsistenciaCitacionRepository
from app.repositories.citacion_repo import CitacionRepository
from app.repositories.comunicado_repo import ComunicadoRepository
from app.repositories.confirmacion_lectura_repo import ConfirmacionLecturaRepository
from app.repositories.curso_repo import CursoRepository
from app.repositories.estudiante_repo import EstudianteRepository
from app.repositories.mensaje_repo import MensajeRepository
from app.repositories.rol_repo import RolRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services.notificador import notificar

PASSWORD_DEMO = "Colegio2026*"

USUARIOS = [
    # clave,  nombre,                        correo,                           rol,            teléfono
    ("coord", "Patricia Herrera Molina",     "coordinacion@colegio.edu.co",    "coordinacion", "3014567890"),
    ("doc1",  "Luis Fernando Martínez",      "lmartinez@colegio.edu.co",       "docente",      "3002223344"),
    ("doc2",  "Carolina Gómez Ríos",         "cgomez@colegio.edu.co",          "docente",      "3003334455"),
    ("doc3",  "Andrés Felipe Ortiz",         "aortiz@colegio.edu.co",          "docente",      "3005556677"),
    ("doc4",  "Diana Marcela Pacheco",       "dpacheco@colegio.edu.co",        "docente",      "3016667788"),
    ("doc5",  "Jorge Iván Barrios",          "jbarrios@colegio.edu.co",        "docente",      "3027778899"),
    ("acu1",  "María Rodríguez",             "maria.rodriguez@correo.com",     "acudiente",    "3101234567"),
    ("acu2",  "Jorge Pérez",                 "jorge.perez@correo.com",         "acudiente",    "3112345678"),
    ("acu3",  "Ana Sánchez",                 "ana.sanchez@correo.com",         "acudiente",    "3123456789"),
    ("acu4",  "Laura Díaz",                  "laura.diaz@correo.com",          "acudiente",    "3134567890"),
    ("acu5",  "Carlos Mendoza Fontalvo",     "carlos.mendoza@correo.com",      "acudiente",    "3145678901"),
    ("acu6",  "Yolanda Castro de la Hoz",    "yolanda.castro@correo.com",      "acudiente",    "3156789012"),
    ("acu7",  "Ricardo Charris",             "ricardo.charris@correo.com",     "acudiente",    "3167890123"),
    ("acu8",  "Paola Ariza Polo",            "paola.ariza@correo.com",         "acudiente",    "3178901234"),
    ("acu9",  "Hernán Cantillo",             "hernan.cantillo@correo.com",     "acudiente",    "3189012345"),
    ("acu10", "Sandra Milena Orozco",        "sandra.orozco@correo.com",       "acudiente",    "3190123456"),
]

CURSOS = [
    # clave, nombre, grado, jornada, director
    ("3A",  "3A",  3,  "manana", "doc4"),
    ("5A",  "5A",  5,  "manana", "doc1"),
    ("6B",  "6B",  6,  "tarde",  "doc2"),
    ("9A",  "9A",  9,  "manana", "doc3"),
    ("11A", "11A", 11, "manana", "doc5"),
]

ESTUDIANTES = [
    # clave, nombre, documento, curso
    ("santiago",  "Santiago Rodríguez",       "1043987001", "5A"),
    ("valentina", "Valentina Rodríguez",      "1043987002", "6B"),
    ("samuel",    "Samuel Pérez Díaz",        "1043987003", "5A"),
    ("isabella",  "Isabella Sánchez",         "1043987004", "6B"),
    ("mateo",     "Mateo Castro Ruiz",        "1043987005", "5A"),
    ("sofia",     "Sofía Mendoza Ariza",      "1043987006", "3A"),
    ("emiliano",  "Emiliano Mendoza Ariza",   "1043987007", "9A"),
    ("mariana",   "Mariana Castro",           "1043987008", "11A"),
    ("tomas",     "Tomás Charris Orozco",     "1043987009", "6B"),
    ("salome",    "Salomé Cantillo",          "1043987010", "3A"),
    ("daniel",    "Daniel Cantillo",          "1043987011", "9A"),
    ("gabriela",  "Gabriela Orozco",          "1043987012", "11A"),
    ("juanjose",  "Juan José Charris",        "1043987013", "9A"),
    ("antonella", "Antonella Ruiz Polo",      "1043987014", "3A"),
]

VINCULOS = [
    # acudiente, estudiante, parentesco, principal
    ("acu1", "santiago", "madre", True), ("acu1", "valentina", "madre", True),
    ("acu2", "samuel", "padre", True), ("acu4", "samuel", "madre", False),
    ("acu3", "isabella", "madre", True),
    ("acu5", "sofia", "padre", True), ("acu5", "emiliano", "padre", True),
    ("acu8", "sofia", "madre", False), ("acu8", "emiliano", "madre", False),
    ("acu6", "mariana", "madre", True),
    ("acu7", "tomas", "padre", True), ("acu7", "juanjose", "padre", True),
    ("acu10", "tomas", "madre", False), ("acu10", "gabriela", "madre", True),
    ("acu9", "salome", "padre", True), ("acu9", "daniel", "padre", True),
    ("acu8", "antonella", "tía", True),
]

COMUNICADOS = [
    # autor, curso (None = general), dias atrás, prioridad, requiere, título, contenido
    ("coord", None, 15, "normal", True, "Bienvenidos a Conecta Escolar",
     "A partir de hoy todas las circulares, citaciones y avisos del colegio llegarán por esta plataforma. "
     "Les pedimos confirmar la lectura de cada comunicado para tener la certeza de que la información llegó a tiempo."),
    ("coord", None, 7, "normal", True, "Calendario de evaluaciones del cuarto periodo",
     "Las evaluaciones del cuarto periodo se realizarán del 3 al 14 de noviembre. El horario detallado por curso "
     "será publicado por cada director de grupo. Recuerden que la asistencia es obligatoria."),
    ("coord", None, 2, "urgente", True, "Entrega de boletines del tercer periodo",
     "La entrega de boletines del tercer periodo será el viernes 24 de octubre de 7:00 a. m. a 11:00 a. m. en el "
     "salón de cada curso. Es indispensable la asistencia del acudiente principal."),
    ("doc1", "5A", 5, "urgente", True, "Salida pedagógica al Museo del Caribe",
     "El jueves 23 de octubre realizaremos la salida pedagógica al Museo del Caribe. Los estudiantes deben asistir "
     "con uniforme de educación física, lonchera y la autorización firmada por el acudiente."),
    ("doc1", "5A", 1, "normal", False, "Materiales para la feria de la ciencia",
     "Para la feria de la ciencia cada grupo necesita: cartulina, marcadores, pegante y los materiales del experimento "
     "que eligió. La feria será el 30 de octubre."),
    ("doc2", "6B", 4, "normal", True, "Taller para padres: uso responsable de redes sociales",
     "Invitamos a los acudientes del 6B al taller sobre acompañamiento en el uso de redes sociales, el martes 21 "
     "de octubre a las 6:00 p. m. en el auditorio."),
    ("doc3", "9A", 6, "normal", True, "Simulacro Pruebas Saber 9°",
     "El miércoles 22 de octubre se aplicará el simulacro de las Pruebas Saber para grado noveno. Los estudiantes "
     "deben traer lápiz número 2, borrador y tajalápiz."),
    ("doc5", "11A", 3, "urgente", True, "Reunión de padres: ceremonia de grado",
     "Citamos a los acudientes del grado 11A a la reunión informativa sobre la ceremonia de grado y los derechos "
     "de grado el sábado 25 de octubre a las 9:00 a. m."),
    ("doc4", "3A", 8, "normal", False, "Plan lector: libro del mes",
     "El libro del mes de octubre es «El principito». Les sugerimos acompañar la lectura en casa durante 20 minutos "
     "diarios. Al final del mes haremos un conversatorio en clase."),
]

MENSAJES_CURSO = [
    ("5A", "doc1", "¡Buenos días, familias del 5A! Por este chat resolveremos las dudas del curso."),
    ("5A", "acu2", "Buenos días, profe. ¿La salida al museo tiene algún costo?"),
    ("5A", "doc1", "No tiene costo, don Jorge. El transporte lo cubre el colegio."),
    ("5A", "acu1", "Gracias, profe. Santiago ya tiene lista la autorización."),
    ("6B", "doc2", "Bienvenidos al chat del 6B. Recuerden revisar las circulares y confirmar la lectura."),
    ("6B", "acu7", "Profe, ¿el taller del martes es solo para acudientes o pueden ir los estudiantes?"),
    ("6B", "doc2", "Es solo para acudientes, don Ricardo. Muchas gracias por preguntar."),
    ("11A", "doc5", "Estimadas familias, el sábado tendremos la reunión de grado. Por favor confirmen asistencia."),
    ("11A", "acu6", "Confirmado, profesor. Allá estaremos."),
]

MENSAJES_DIRECTOS = [
    ("acu1", "doc2", "Buenas tardes, profesora. Valentina estuvo enferma ayer; le envío la excusa médica mañana."),
    ("doc2", "acu1", "Gracias por avisar, señora María. Que se mejore pronto."),
    ("acu3", "doc2", "Profesora, ¿podría revisar la nota de matemáticas de Isabella? Creo que hubo un error."),
    ("doc3", "acu5", "Don Carlos, Emiliano ha mejorado mucho en física. ¡Felicitaciones!"),
    ("acu9", "coord", "Buenos días. ¿Cuándo abren las inscripciones para la escuela de fútbol?"),
]


def _sql(consulta, valores=()):
    with get_cursor() as cur:
        cur.execute(consulta, valores)


def sembrar() -> dict:
    random.seed(2026)
    ahora = ahora_local()
    roles = {r["nombre"]: r["id"] for r in RolRepository().listar()}
    usuarios_repo = UsuarioRepository()
    hash_demo = hashear_password(PASSWORD_DEMO)

    u = {}
    for clave, nombre, correo, rol, tel in USUARIOS:
        u[clave] = usuarios_repo.obtener_por_correo(correo) or usuarios_repo.crear({
            "nombre": nombre, "correo": correo, "password_hash": hash_demo, "telefono": tel, "rol_id": roles[rol]})

    cursos_repo = CursoRepository()
    c = {clave: cursos_repo.crear({"nombre": nombre, "grado": grado, "jornada": jornada,
                                   "director_id": u[dir_]["id"]})
         for clave, nombre, grado, jornada, dir_ in CURSOS}

    est_repo = EstudianteRepository()
    e = {clave: est_repo.crear({"nombre": nombre, "documento": doc, "curso_id": c[curso]["id"]})
         for clave, nombre, doc, curso in ESTUDIANTES}

    vinc = AcudienteEstudianteRepository()
    for acu, est, parentesco, principal in VINCULOS:
        vinc.crear({"acudiente_id": u[acu]["id"], "estudiante_id": e[est]["id"],
                    "parentesco": parentesco, "es_principal": principal})

    # ---------------------------------------------------- comunicados
    com_repo = ComunicadoRepository()
    conf_repo = ConfirmacionLecturaRepository()
    comunicados = {}
    for autor, curso, dias, prioridad, requiere, titulo, contenido in COMUNICADOS:
        com = com_repo.crear({"titulo": titulo, "contenido": contenido, "autor_id": u[autor]["id"],
                              "curso_id": c[curso]["id"] if curso else None,
                              "prioridad": prioridad, "requiere_confirmacion": requiere})
        fecha = (ahora - timedelta(days=dias)).replace(hour=random.randint(7, 17), minute=random.choice([0, 15, 30, 45]))
        _sql("UPDATE comunicados SET fecha_publicacion = %s, creado = %s, modificado = %s WHERE id = %s",
             (fecha, fecha, fecha, com["id"]))
        destinatarios = [d["id"] for d in com_repo.destinatarios(com["curso_id"])]
        notifs = notificar(destinatarios, "comunicado",
                           ("URGENTE: " if prioridad == "urgente" else "") + titulo, contenido[:250], com["id"])
        _sql("UPDATE notificaciones SET fecha = %s, creado = %s WHERE referencia_id = %s AND tipo = 'comunicado'",
             (fecha, fecha, com["id"]))
        # Las circulares más antiguas tienen más confirmaciones (lectura realista, no del 100 %)
        if requiere:
            probabilidad = min(0.85, 0.35 + dias * 0.06)
            for acu_id in destinatarios:
                if random.random() < probabilidad:
                    conf = conf_repo.crear({"comunicado_id": com["id"], "usuario_id": acu_id})
                    fc = fecha + timedelta(hours=random.randint(1, 30))
                    _sql("UPDATE confirmaciones_lectura SET fecha_confirmacion = %s, creado = %s WHERE id = %s",
                         (min(fc, ahora), min(fc, ahora), conf["id"]))
                    _sql("""UPDATE notificaciones SET leido = TRUE
                            WHERE usuario_id = %s AND referencia_id = %s AND tipo = 'comunicado'""",
                         (acu_id, com["id"]))
        comunicados[titulo] = com

    # ---------------------------------------------------- mensajes
    msg = MensajeRepository()
    base = ahora - timedelta(days=3)
    for i, (curso, autor, texto) in enumerate(MENSAJES_CURSO):
        m = msg.crear({"remitente_id": u[autor]["id"], "curso_id": c[curso]["id"], "contenido": texto})
        f = base + timedelta(hours=i * 3)
        _sql("UPDATE mensajes SET fecha_envio = %s, creado = %s WHERE id = %s", (f, f, m["id"]))
    for i, (de, para, texto) in enumerate(MENSAJES_DIRECTOS):
        m = msg.crear({"remitente_id": u[de]["id"], "destinatario_id": u[para]["id"], "contenido": texto,
                       "leido": i % 2 == 1})
        f = base + timedelta(hours=i * 5 + 1)
        _sql("UPDATE mensajes SET fecha_envio = %s, creado = %s WHERE id = %s", (f, f, m["id"]))

    # ---------------------------------------------------- citaciones
    cit_repo = CitacionRepository()
    asis_repo = AsistenciaCitacionRepository()

    def dia(delta, hora, minuto=0):
        return (ahora + timedelta(days=delta)).replace(hour=hora, minute=minuto, second=0, microsecond=0)

    citaciones_def = [
        # estudiante, docente, acudiente, motivo, fecha, lugar, estado, asistio
        ("samuel", "doc1", None, "Seguimiento académico del tercer periodo", dia(3, 7, 30),
         "Sala de profesores", "pendiente", None),
        ("isabella", "doc2", "acu3", "Revisión de notas de matemáticas", dia(2, 14, 0),
         "Coordinación académica", "confirmada", None),
        ("emiliano", "doc3", None, "Reconocimiento por desempeño en física", dia(6, 8, 0),
         "Salón 9A", "pendiente", None),
        ("tomas", "doc2", None, "Llegadas tarde reiteradas", dia(1, 13, 30),
         "Coordinación de convivencia", "pendiente", None),
        ("valentina", "doc2", "acu1", "Seguimiento por inasistencias de la semana pasada", dia(4, 15, 0),
         "Salón 6B", "pendiente", None),
        ("mariana", "doc5", "acu6", "Orientación vocacional y opciones de universidad", dia(8, 9, 0),
         "Oficina de orientación", "pendiente", None),
        ("santiago", "doc1", "acu1", "Acompañamiento en lectura", dia(-6, 7, 0),
         "Sala de profesores", "realizada", True),
        ("daniel", "doc3", None, "Incumplimiento de tareas de química", dia(-4, 10, 0),
         "Salón 9A", "realizada", False),
        ("salome", "doc4", None, "Adaptación al grupo", dia(-2, 8, 30),
         "Salón 3A", "cancelada", None),
    ]
    citaciones = []
    for est, doc, acu, motivo, fecha, lugar, estado, asistio in citaciones_def:
        cit = cit_repo.crear({"estudiante_id": e[est]["id"], "docente_id": u[doc]["id"],
                              "acudiente_id": u[acu]["id"] if acu else None, "motivo": motivo,
                              "fecha_hora": fecha, "lugar": lugar, "estado_citacion": estado})
        citaciones.append(cit)
        creada = min(fecha, ahora) - timedelta(days=3)
        _sql("UPDATE citaciones SET creado = %s WHERE id = %s", (creada, cit["id"]))
        destino = cit_repo.ids_acudientes_destino(cit)
        notificar(destino, "citacion", f"Citación: {ESTUD[est]}",
                  f"{motivo} · {fecha.strftime('%d/%m/%Y %I:%M %p')} · {lugar}", cit["id"])
        if asistio is not None:
            asis_repo.crear({"citacion_id": cit["id"], "asistio": asistio, "registrado_por": u[doc]["id"],
                             "observaciones": "El acudiente se comprometió a reforzar en casa." if asistio
                             else "El acudiente no asistió; se reprogramará por teléfono."})
        if estado != "pendiente":
            _sql("""UPDATE notificaciones SET leido = TRUE
                    WHERE referencia_id = %s AND tipo = 'citacion'""", (cit["id"],))

    return {"usuarios": u, "cursos": c, "estudiantes": e, "comunicados": comunicados,
            "citacion": citaciones[0], "citaciones": citaciones}


ESTUD = {clave: nombre for clave, nombre, _, _ in ESTUDIANTES}


if __name__ == "__main__":
    if not settings.DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el archivo .env")
    sembrar()
    print("✔ Datos de demostración cargados.\n")
    print(f"Usuarios de prueba (contraseña: {PASSWORD_DEMO}):")
    for _, nombre, correo, rol, _ in USUARIOS:
        print(f"  {rol:<13} {correo:<32} {nombre}")
