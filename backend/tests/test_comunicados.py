from app.repositories.notificacion_repo import NotificacionRepository


SALIDA = "Salida pedagógica al Museo del Caribe"
GENERAL = "Bienvenidos a Conecta Escolar"


def _notifs(usuario_id):
    return NotificacionRepository().de_usuario(usuario_id)


def _nuevo_5a(client, login, datos, **extra):
    r = client.post("/comunicados/", headers=login("doc1"), json={
        "titulo": "Horario de la semana cultural", "contenido": "Se publica el horario.",
        "curso_id": datos["cursos"]["5A"]["id"], **extra})
    assert r.status_code == 201
    return r.json()["id"]


def test_publicar_comunicado_notifica_solo_a_acudientes_del_curso(client, login, datos):
    u, c = datos["usuarios"], datos["cursos"]
    antes = {k: len(_notifs(u[k]["id"])) for k in ("acu1", "acu2", "acu3", "acu4")}
    r = client.post("/comunicados/", headers=login("doc2"), json={
        "titulo": "Tarea de matemáticas", "contenido": "Página 45, ejercicios 1 a 10.", "curso_id": c["6B"]["id"]})
    assert r.status_code == 201
    assert r.json()["autor_nombre"] == "Carolina Gómez Ríos" and r.json()["curso_nombre"] == "6B"
    despues = {k: len(_notifs(u[k]["id"])) for k in antes}
    # 6B: María (Valentina), Ana (Isabella). Jorge y Laura (5A) no.
    assert despues["acu1"] == antes["acu1"] + 1 and despues["acu3"] == antes["acu3"] + 1
    assert despues["acu2"] == antes["acu2"] and despues["acu4"] == antes["acu4"]


def test_docente_no_publica_circular_general(client, login):
    r = client.post("/comunicados/", headers=login("doc1"), json={"titulo": "General", "contenido": "x"})
    assert r.status_code == 403
    assert client.post("/comunicados/", headers=login("coord"),
                       json={"titulo": "General", "contenido": "x"}).status_code == 201


def test_acudiente_no_puede_publicar(client, login, datos):
    r = client.post("/comunicados/", headers=login("maria"),
                    json={"titulo": "Hola", "contenido": "x", "curso_id": datos["cursos"]["5A"]["id"]})
    assert r.status_code == 403


def test_visibilidad_de_comunicados_por_acudiente(client, login, datos):
    titulos_ana = {c["titulo"] for c in client.get("/comunicados/", headers=login("ana")).json()}
    assert GENERAL in titulos_ana          # general
    assert SALIDA not in titulos_ana       # es del 5A
    salida = datos["comunicados"][SALIDA]["id"]
    assert client.get(f"/comunicados/{salida}", headers=login("ana")).status_code == 404
    assert client.get(f"/comunicados/{salida}", headers=login("jorge")).status_code == 200


def test_confirmar_lectura_una_sola_vez(client, login, datos):
    salida = _nuevo_5a(client, login, datos)
    h = login("jorge")
    assert client.get(f"/comunicados/{salida}", headers=h).json()["confirmado_por_mi"] is False
    assert client.post(f"/comunicados/{salida}/confirmar", headers=h).status_code == 201
    assert client.post(f"/comunicados/{salida}/confirmar", headers=h).status_code == 409
    assert client.get(f"/comunicados/{salida}", headers=h).json()["confirmado_por_mi"] is True
    # Acudiente de otro curso no puede confirmar
    assert client.post(f"/comunicados/{salida}/confirmar", headers=login("ana")).status_code == 404


def test_estado_de_lectura_quien_leyo_y_quien_no(client, login, datos):
    salida = _nuevo_5a(client, login, datos)
    client.post(f"/comunicados/{salida}/confirmar", headers=login("jorge"))
    r = client.get(f"/comunicados/{salida}/lecturas", headers=login("doc1")).json()
    # 5A: María (Santiago), Jorge y Laura (Samuel). Mateo no tiene acudiente.
    assert r["destinatarios"] == 3 and r["confirmados"] == 1 and r["porcentaje"] == 33.3
    assert {d["nombre"] for d in r["detalle"] if not d["confirmado"]} == {"María Rodríguez", "Laura Díaz"}
    assert client.get(f"/comunicados/{salida}/lecturas", headers=login("jorge")).status_code == 403


def test_editar_y_archivar_solo_autor_o_coordinacion(client, login, datos):
    salida = datos["comunicados"][SALIDA]["id"]
    assert client.patch(f"/comunicados/{salida}", json={"titulo": "Cambio"}, headers=login("doc2")).status_code == 403
    r = client.patch(f"/comunicados/{salida}", json={"titulo": "Salida pedagógica (actualizado)"},
                     headers=login("doc1"))
    assert r.status_code == 200 and r.json()["titulo"].endswith("(actualizado)")
    assert r.json()["modificado"] > r.json()["creado"]          # lo actualizó el TRIGGER
    assert client.delete(f"/comunicados/{salida}", headers=login("coord")).status_code == 200
    assert client.get(f"/comunicados/{salida}", headers=login("jorge")).status_code == 404


def test_comunicado_que_no_requiere_confirmacion(client, login, datos):
    r = client.post("/comunicados/", headers=login("doc1"), json={
        "titulo": "Recordatorio", "contenido": "Mañana no hay clase.", "curso_id": datos["cursos"]["5A"]["id"],
        "requiere_confirmacion": False})
    assert client.post(f"/comunicados/{r.json()['id']}/confirmar", headers=login("jorge")).status_code == 400
