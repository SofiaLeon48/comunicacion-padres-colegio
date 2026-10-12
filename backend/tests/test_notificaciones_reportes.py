def test_contador_y_marcar_leidas(client, login):
    h = login("jorge")
    total = client.get("/notificaciones/contador", headers=h).json()["no_leidas"]
    assert total >= 2   # 2 comunicados + 1 citación del seed
    primera = client.get("/notificaciones/", headers=h).json()[0]
    assert client.patch(f"/notificaciones/{primera['id']}/leer", headers=h).json()["leido"] is True
    assert client.get("/notificaciones/contador", headers=h).json()["no_leidas"] == total - 1
    client.patch("/notificaciones/leer-todas", headers=h)
    assert client.get("/notificaciones/contador", headers=h).json()["no_leidas"] == 0


def test_no_puede_leer_notificacion_ajena(client, login):
    ajena = client.get("/notificaciones/", headers=login("maria")).json()[0]["id"]
    assert client.patch(f"/notificaciones/{ajena}/leer", headers=login("jorge")).status_code == 404


def test_aviso_del_sistema_por_rol(client, login):
    r = client.post("/notificaciones/", headers=login("coord"),
                    json={"titulo": "Simulacro de evacuación", "contenido": "Jueves 9 a.m.", "roles": ["docente"]})
    assert r.status_code == 201 and "2 usuarios" in r.json()["mensaje"]
    assert client.get("/notificaciones/", headers=login("doc2")).json()[0]["tipo"] == "sistema"
    assert client.post("/notificaciones/", headers=login("doc1"),
                       json={"titulo": "Hola", "contenido": "x", "roles": ["acudiente"]}).status_code == 403


def test_reportes(client, login, datos):
    client.post(f"/comunicados/{datos['comunicados']['salida']['id']}/confirmar", headers=login("jorge"))
    h = login("coord")
    resumen = client.get("/reportes/resumen", headers=h).json()
    assert resumen["estudiantes"] == 5 and resumen["cursos"] == 2 and resumen["citaciones_proximas"] == 1
    lectura = {x["titulo"]: x for x in client.get("/reportes/lectura-comunicados", headers=h).json()}
    assert lectura["Salida pedagógica al Museo del Caribe"]["porcentaje_lectura"] == 33.3
    assert lectura["Bienvenida al nuevo canal oficial"]["destinatarios"] == 4
    pendientes = client.get("/reportes/acudientes-pendientes", headers=h).json()
    assert pendientes[0]["nombre"] in ("María Rodríguez", "Laura Díaz") and pendientes[0]["pendientes"] == 2
    for ruta in ("/reportes/citaciones", "/reportes/actividad-cursos", "/reportes/actividad-reciente"):
        assert client.get(ruta, headers=h).status_code == 200
    assert client.get("/reportes/resumen", headers=login("maria")).status_code == 403


def test_logs_de_actividad_automaticos(client, login, datos):
    client.post(f"/comunicados/{datos['comunicados']['salida']['id']}/confirmar", headers=login("jorge"))
    logs = client.get("/logs/", headers=login("admin")).json()
    acciones = {l["accion"] for l in logs}
    assert {"login", "confirmar_lectura"} <= acciones
    assert client.get("/logs/", headers=login("doc1")).status_code == 403


def test_salud_y_cors(client):
    assert client.get("/salud").json()["base_de_datos"] == "ok"
    r = client.options("/comunicados/", headers={"Origin": "http://localhost:5173",
                                                 "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
