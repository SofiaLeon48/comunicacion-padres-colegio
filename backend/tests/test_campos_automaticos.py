"""Los datos automáticos nunca se piden: si alguien los envía, la API los ignora."""


def test_comunicado_ignora_campos_automaticos(client, login, datos):
    r = client.post("/comunicados/", headers=login("doc1"), json={
        "titulo": "Campos automáticos", "contenido": "x", "grupo_id": datos["grupos"]["5A"]["id"],
        "id": 9999, "autor_id": 1, "fecha_publicacion": "2000-01-01T00:00:00",
        "creado": "2000-01-01T00:00:00", "estado": "inactivo"})
    assert r.status_code == 201
    c = r.json()
    assert c["id"] != 9999
    assert c["autor_id"] == datos["usuarios"]["doc1"]["id"]
    assert not c["fecha_publicacion"].startswith("2000")
    assert c["estado"] == "activo"


def test_mensaje_ignora_remitente_y_fecha(client, login, datos):
    r = client.post("/mensajes/", headers=login("doc1"), json={
        "grupo_id": datos["grupos"]["5A"]["id"], "contenido": "hola",
        "remitente_id": 1, "fecha_envio": "2000-01-01T00:00:00", "leido": True})
    assert r.status_code == 201
    m = r.json()
    assert m["remitente_id"] == datos["usuarios"]["doc1"]["id"]
    assert not m["fecha_envio"].startswith("2000") and m["leido"] is False


def test_grupo_sin_anio_toma_el_actual(client, login):
    r = client.post("/grupos/", headers=login("coord"), json={"nombre": "7C", "grado": 7})
    assert r.status_code == 201 and r.json()["anio_lectivo"] >= 2026


def test_editar_no_cambia_el_estado(client, login, datos):
    """El estado solo se cambia con desactivar / reactivar, no al editar."""
    est = datos["estudiantes"]["samuel"]
    r = client.patch(f"/estudiantes/{est['id']}", headers=login("coord"),
                     json={"nombre": "Samuel Pérez Díaz", "estado": "inactivo"})
    assert r.status_code == 200 and r.json()["estado"] == "activo"


def test_modulo_se_desactiva_y_reactiva(client, login):
    h = login("coord")
    mods = {m["clave"]: m for m in client.get("/configuracion/modulos", headers=h).json()}
    assert client.delete(f"/configuracion/modulos/{mods['configuracion']['id']}", headers=h).status_code == 400
    rid = mods["reportes"]["id"]
    assert client.delete(f"/configuracion/modulos/{rid}", headers=h).status_code == 200
    assert client.post(f"/configuracion/modulos/{rid}/reactivar", headers=h).status_code == 200
    assert "reportes" in [m["clave"] for m in client.get("/auth/mis-modulos", headers=login("doc1")).json()]
