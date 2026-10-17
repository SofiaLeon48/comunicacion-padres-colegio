def test_crear_grupo_y_duplicado(client, login, datos):
    h = login("coord")
    nuevo = {"nombre": "7C", "grado": 7, "jornada": "manana", "director_id": datos["usuarios"]["doc1"]["id"]}
    r = client.post("/grupos/", json=nuevo, headers=h)
    assert r.status_code == 201 and r.json()["anio_lectivo"] >= 2026
    assert client.post("/grupos/", json=nuevo, headers=h).status_code == 409


def test_grupo_valores_invalidos(client, login, datos):
    h = login("coord")
    assert client.post("/grupos/", json={"nombre": "X", "grado": 15}, headers=h).status_code == 422
    assert client.post("/grupos/", json={"nombre": "X", "grado": 3, "jornada": "noche"}, headers=h).status_code == 422
    # El director debe ser docente
    r = client.post("/grupos/", json={"nombre": "8A", "grado": 8,
                                      "director_id": datos["usuarios"]["acu1"]["id"]}, headers=h)
    assert r.status_code == 400


def test_acudiente_solo_ve_sus_grupos_e_hijos(client, login):
    grupos_jorge = client.get("/catalogos/grupos", headers=login("jorge")).json()
    assert [c["nombre"] for c in grupos_jorge] == ["5A"]
    grupos_maria = client.get("/catalogos/grupos", headers=login("maria")).json()
    assert {c["nombre"] for c in grupos_maria} == {"5A", "6B"}
    hijos = client.get("/estudiantes/", headers=login("maria")).json()
    assert {e["nombre"] for e in hijos} == {"Santiago Rodríguez", "Valentina Rodríguez"}
    assert len(client.get("/estudiantes/", headers=login("doc1")).json()) == 14


def test_acudiente_no_ve_estudiante_ajeno(client, login, datos):
    isabella = datos["estudiantes"]["isabella"]["id"]
    assert client.get(f"/estudiantes/{isabella}", headers=login("jorge")).status_code == 404
    assert client.get(f"/estudiantes/{isabella}", headers=login("ana")).status_code == 200


def test_estudiante_con_grupo_inexistente_400(client, login):
    r = client.post("/estudiantes/", json={"nombre": "Nuevo Niño", "documento": "999999", "grupo_id": 999},
                    headers=login("coord"))
    assert r.status_code == 400


def test_no_se_desactiva_grupo_con_estudiantes(client, login, datos):
    r = client.delete(f"/grupos/{datos['grupos']['5A']['id']}", headers=login("coord"))
    assert r.status_code == 409


def test_vinculos_acudiente_estudiante(client, login, datos):
    h = login("coord")
    u, e = datos["usuarios"], datos["estudiantes"]
    # Duplicado
    r = client.post("/acudientes-estudiantes/", headers=h,
                    json={"acudiente_id": u["acu2"]["id"], "estudiante_id": e["samuel"]["id"]})
    assert r.status_code == 409
    # Un docente no puede ser acudiente
    r = client.post("/acudientes-estudiantes/", headers=h,
                    json={"acudiente_id": u["doc1"]["id"], "estudiante_id": e["mateo"]["id"]})
    assert r.status_code == 400
    # Crear, desactivar y volver a crear => se reactiva el mismo registro
    r = client.post("/acudientes-estudiantes/", headers=h,
                    json={"acudiente_id": u["acu3"]["id"], "estudiante_id": e["mateo"]["id"], "parentesco": "tía"})
    assert r.status_code == 201
    vid = r.json()["id"]
    assert client.delete(f"/acudientes-estudiantes/{vid}", headers=h).status_code == 200
    r2 = client.post("/acudientes-estudiantes/", headers=h,
                     json={"acudiente_id": u["acu3"]["id"], "estudiante_id": e["mateo"]["id"]})
    assert r2.status_code == 201 and r2.json()["id"] == vid and r2.json()["estado"] == "activo"


def test_acudientes_de_un_estudiante(client, login, datos):
    samuel = datos["estudiantes"]["samuel"]["id"]
    r = client.get(f"/estudiantes/{samuel}/acudientes", headers=login("doc1"))
    assert {a["nombre"] for a in r.json()} == {"Jorge Pérez", "Laura Díaz"}
