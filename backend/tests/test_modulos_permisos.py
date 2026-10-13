"""Menú y permisos cargados desde la base de datos (tabla rol_modulo)."""


def test_mis_modulos_por_rol(client, login):
    claves = lambda q: [m["clave"] for m in client.get("/auth/mis-modulos", headers=login(q)).json()]
    assert len(claves("coord")) == 9
    assert claves("doc1") == ["inicio", "comunicados", "mensajes", "citaciones", "estudiantes", "cursos", "reportes"]
    assert claves("jorge") == ["inicio", "comunicados", "mensajes", "citaciones", "estudiantes"]


def test_api_respeta_los_modulos_del_rol(client, login):
    assert client.get("/cursos/", headers=login("jorge")).status_code == 403
    assert client.get("/usuarios/", headers=login("doc1")).status_code == 403
    assert client.get("/reportes/resumen", headers=login("maria")).status_code == 403
    assert client.get("/configuracion/permisos", headers=login("doc1")).status_code == 403


def test_configuracion_da_y_quita_modulos(client, login):
    h = login("coord")
    matriz = client.get("/configuracion/permisos", headers=h).json()
    celda = next(x for x in matriz if x["rol"] == "acudiente" and x["clave"] == "cursos")
    assert celda["permitido"] is False
    # Coordinación le da el módulo Cursos al rol acudiente
    r = client.put("/configuracion/permisos", headers=h,
                   json={"rol_id": celda["rol_id"], "modulo_id": celda["modulo_id"], "permitido": True})
    assert r.status_code == 200
    assert "cursos" in [m["clave"] for m in client.get("/auth/mis-modulos", headers=login("jorge")).json()]
    assert client.get("/cursos/", headers=login("jorge")).status_code == 200
    # ...y se lo quita
    client.put("/configuracion/permisos", headers=h,
               json={"rol_id": celda["rol_id"], "modulo_id": celda["modulo_id"], "permitido": False})
    assert client.get("/cursos/", headers=login("jorge")).status_code == 403


def test_coordinacion_no_se_bloquea_a_si_misma(client, login):
    h = login("coord")
    celda = next(x for x in client.get("/configuracion/permisos", headers=h).json()
                 if x["rol"] == "coordinacion" and x["clave"] == "configuracion")
    r = client.put("/configuracion/permisos", headers=h,
                   json={"rol_id": celda["rol_id"], "modulo_id": celda["modulo_id"], "permitido": False})
    assert r.status_code == 400


def test_modulo_desactivado_desaparece_del_menu(client, login):
    h = login("coord")
    reportes = next(m for m in client.get("/configuracion/modulos", headers=h).json() if m["clave"] == "reportes")
    assert client.patch(f"/configuracion/modulos/{reportes['id']}", json={"estado": "inactivo"},
                        headers=h).status_code == 200
    assert "reportes" not in [m["clave"] for m in client.get("/auth/mis-modulos", headers=login("doc1")).json()]
    assert client.get("/reportes/resumen", headers=login("doc1")).status_code == 403


def test_catalogos_filtrados_por_rol(client, login):
    contactos = client.get("/catalogos/contactos", headers=login("jorge")).json()
    assert contactos and all(c["rol"] in ("docente", "coordinacion") for c in contactos)
    assert {c["nombre"] for c in client.get("/catalogos/cursos", headers=login("maria")).json()} == {"5A", "6B"}
    assert client.get("/catalogos/acudientes", headers=login("maria")).status_code == 403
    assert all("etiqueta" in x for x in client.get("/catalogos/estudiantes", headers=login("doc1")).json())


def test_inicio_segun_rol(client, login):
    acu = client.get("/inicio/resumen", headers=login("maria")).json()
    assert {h["nombre"] for h in acu["hijos"]} == {"Santiago Rodríguez", "Valentina Rodríguez"}
    assert "comunicados_pendientes" in acu
    doc = client.get("/inicio/resumen", headers=login("doc1")).json()
    assert doc["mis_cursos"][0]["nombre"] == "5A"
    coord = client.get("/inicio/resumen", headers=login("coord")).json()
    assert coord["indicadores"]["estudiantes"] == 14
