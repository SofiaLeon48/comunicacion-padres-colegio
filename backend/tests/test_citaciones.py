from datetime import datetime, timedelta


def _futuro(dias=5):
    return (datetime.now() + timedelta(days=dias)).replace(microsecond=0).isoformat()


def test_crear_citacion_notifica_a_todos_los_acudientes(client, login, datos):
    mateo_vinc = client.post("/acudientes-estudiantes/", headers=login("coord"), json={
        "acudiente_id": datos["usuarios"]["acu3"]["id"], "estudiante_id": datos["estudiantes"]["samuel"]["id"]})
    assert mateo_vinc.status_code == 201
    r = client.post("/citaciones/", headers=login("doc1"), json={
        "estudiante_id": datos["estudiantes"]["samuel"]["id"], "motivo": "Convivencia",
        "fecha_hora": _futuro(), "lugar": "Coordinación"})
    assert r.status_code == 201
    assert r.json()["docente_nombre"] == "Luis Fernando Martínez" and r.json()["estado_citacion"] == "pendiente"
    for quien in ("jorge", "laura", "ana"):
        notifs = client.get("/notificaciones/", headers=login(quien)).json()
        assert any(n["tipo"] == "citacion" and n["referencia_id"] == r.json()["id"] for n in notifs), quien


def test_citacion_en_el_pasado_400(client, login, datos):
    r = client.post("/citaciones/", headers=login("doc1"), json={
        "estudiante_id": datos["estudiantes"]["samuel"]["id"], "motivo": "Tarde",
        "fecha_hora": "2020-01-01T08:00:00"})
    assert r.status_code == 400


def test_citacion_a_acudiente_no_vinculado_400(client, login, datos):
    r = client.post("/citaciones/", headers=login("doc1"), json={
        "estudiante_id": datos["estudiantes"]["samuel"]["id"], "acudiente_id": datos["usuarios"]["acu3"]["id"],
        "motivo": "Revisión", "fecha_hora": _futuro()})
    assert r.status_code == 400


def test_visibilidad_de_citaciones_por_rol(client, login, datos):
    cid = datos["citacion"]["id"]
    assert client.get(f"/citaciones/{cid}", headers=login("jorge")).status_code == 200
    assert client.get(f"/citaciones/{cid}", headers=login("maria")).status_code == 404
    assert client.get(f"/citaciones/{cid}", headers=login("doc2")).status_code == 404
    assert len(client.get("/citaciones/", headers=login("coord")).json()) == 9
    assert {c["estudiante_nombre"] for c in client.get("/citaciones/", headers=login("doc2")).json()} == \
        {"Isabella Sánchez", "Tomás Charris Orozco", "Valentina Rodríguez"}


def test_calendario_por_rango_de_fechas(client, login):
    hoy = datetime.now()
    dentro = client.get("/citaciones/", headers=login("coord"),
                        params={"desde": hoy.isoformat(), "hasta": (hoy + timedelta(days=30)).isoformat()})
    fuera = client.get("/citaciones/", headers=login("coord"),
                       params={"desde": (hoy + timedelta(days=30)).isoformat()})
    assert len(dentro.json()) == 6 and fuera.json() == []


def test_acudiente_confirma_pero_no_cancela(client, login, datos):
    cid = datos["citacion"]["id"]
    assert client.patch(f"/citaciones/{cid}/estado", json={"estado_citacion": "cancelada"},
                        headers=login("jorge")).status_code == 403
    r = client.patch(f"/citaciones/{cid}/estado", json={"estado_citacion": "confirmada"}, headers=login("jorge"))
    assert r.status_code == 200 and r.json()["estado_citacion"] == "confirmada"
    notifs = client.get("/notificaciones/", headers=login("doc1")).json()
    assert any(n["titulo"] == "Citación confirmada" for n in notifs)


def test_asistencia_es_1_a_1_y_marca_realizada(client, login, datos):
    cid = datos["citacion"]["id"]
    h = login("doc1")
    r = client.post(f"/citaciones/{cid}/asistencia", json={"asistio": True, "observaciones": "Muy receptivos"},
                    headers=h)
    assert r.status_code == 201
    assert client.post(f"/citaciones/{cid}/asistencia", json={"asistio": False}, headers=h).status_code == 409
    c = client.get(f"/citaciones/{cid}", headers=h).json()
    assert c["estado_citacion"] == "realizada" and c["asistio"] is True
    assert client.patch(f"/citaciones/{cid}/asistencia", json={"observaciones": "Editado"},
                        headers=h).json()["observaciones"] == "Editado"


def test_reprogramar_y_cancelar(client, login, datos):
    cid = datos["citacion"]["id"]
    assert client.patch(f"/citaciones/{cid}", json={"fecha_hora": _futuro(10)}, headers=login("doc2")).status_code == 404
    assert client.patch(f"/citaciones/{cid}", json={"fecha_hora": _futuro(10)}, headers=login("doc1")).status_code == 200
    r = client.patch(f"/citaciones/{cid}/estado", json={"estado_citacion": "cancelada"}, headers=login("doc1"))
    assert r.json()["estado_citacion"] == "cancelada"
    titulos = [n["titulo"] for n in client.get("/notificaciones/", headers=login("laura")).json()]
    assert any(t.startswith("Citación reprogramada") for t in titulos)
    assert any(t.startswith("Citación cancelada") for t in titulos)
    assert client.post(f"/citaciones/{cid}/asistencia", json={"asistio": True},
                       headers=login("doc1")).status_code == 400
