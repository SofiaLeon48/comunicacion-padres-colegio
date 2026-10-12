def test_chat_del_curso_solo_para_miembros(client, login, datos):
    c5a = datos["cursos"]["5A"]["id"]
    chat = client.get(f"/mensajes/curso/{c5a}", headers=login("jorge"))
    assert chat.status_code == 200 and len(chat.json()) == 2
    assert chat.json()[0]["remitente_nombre"] == "Luis Martínez"     # orden cronológico
    assert client.get(f"/mensajes/curso/{c5a}", headers=login("ana")).status_code == 403
    r = client.post("/mensajes/", json={"curso_id": c5a, "contenido": "Hola a todos"}, headers=login("laura"))
    assert r.status_code == 201 and r.json()["remitente_rol"] == "acudiente"
    assert client.post("/mensajes/", json={"curso_id": c5a, "contenido": "Intruso"},
                       headers=login("ana")).status_code == 403


def test_mensaje_debe_tener_un_solo_destino(client, login, datos):
    h = login("doc1")
    assert client.post("/mensajes/", json={"contenido": "sin destino"}, headers=h).status_code == 422
    assert client.post("/mensajes/", json={"contenido": "doble", "curso_id": datos["cursos"]["5A"]["id"],
                                           "destinatario_id": datos["usuarios"]["acu1"]["id"]},
                       headers=h).status_code == 422


def test_mensaje_directo_notifica_y_se_marca_leido(client, login, datos):
    u = datos["usuarios"]
    r = client.post("/mensajes/", json={"destinatario_id": u["acu2"]["id"], "contenido": "Don Jorge, ¿podemos hablar?"},
                    headers=login("doc1"))
    assert r.status_code == 201
    notifs = client.get("/notificaciones/?solo_no_leidas=true", headers=login("jorge")).json()
    assert any(n["tipo"] == "mensaje" and "Luis Martínez" in n["titulo"] for n in notifs)

    bandeja = client.get("/mensajes/directos", headers=login("jorge")).json()
    assert bandeja[0]["contraparte_nombre"] == "Luis Martínez" and bandeja[0]["no_leidos"] == 1
    conv = client.get(f"/mensajes/directos/{u['doc1']['id']}", headers=login("jorge")).json()
    assert conv[-1]["contenido"] == "Don Jorge, ¿podemos hablar?"
    assert client.get("/mensajes/directos", headers=login("jorge")).json()[0]["no_leidos"] == 0


def test_acudiente_no_escribe_a_otro_acudiente(client, login, datos):
    r = client.post("/mensajes/", json={"destinatario_id": datos["usuarios"]["acu3"]["id"], "contenido": "hola"},
                    headers=login("maria"))
    assert r.status_code == 403


def test_no_mensaje_a_si_mismo(client, login, datos):
    r = client.post("/mensajes/", json={"destinatario_id": datos["usuarios"]["doc1"]["id"], "contenido": "yo"},
                    headers=login("doc1"))
    assert r.status_code == 400


def test_editar_y_eliminar_mensajes(client, login, datos):
    c5a = datos["cursos"]["5A"]["id"]
    m = client.post("/mensajes/", json={"curso_id": c5a, "contenido": "Error de tipeo"}, headers=login("jorge")).json()
    assert client.patch(f"/mensajes/{m['id']}", json={"contenido": "x"}, headers=login("laura")).status_code == 403
    assert client.patch(f"/mensajes/{m['id']}", json={"contenido": "Corregido"},
                        headers=login("jorge")).json()["contenido"] == "Corregido"
    assert client.delete(f"/mensajes/{m['id']}", headers=login("coord")).status_code == 200
    assert all(x["id"] != m["id"] for x in client.get(f"/mensajes/curso/{c5a}", headers=login("jorge")).json())
