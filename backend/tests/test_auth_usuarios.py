from scripts.seed import PASSWORD_DEMO


def _login(client, correo, rol, password=PASSWORD_DEMO):
    return client.post("/auth/login", json={"correo": correo, "password": password, "rol": rol})


def test_roles_publicos_para_el_login(client):
    r = client.get("/auth/roles")
    assert r.status_code == 200
    assert [x["nombre"] for x in r.json()] == ["coordinacion", "docente", "acudiente"]


def test_login_con_rol_devuelve_token_y_menu(client):
    r = _login(client, "COORDINACION@colegio.edu.co", "coordinacion")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["access_token"] and cuerpo["usuario"]["rol"] == "coordinacion"
    assert "password_hash" not in cuerpo["usuario"]
    assert len(cuerpo["modulos"]) == 9 and cuerpo["modulos"][0]["clave"] == "inicio"


def test_login_con_rol_equivocado_403(client):
    assert _login(client, "jorge.perez@correo.com", "docente").status_code == 403


def test_login_incorrecto_401(client):
    assert _login(client, "coordinacion@colegio.edu.co", "coordinacion", "malisima").status_code == 401


def test_login_swagger_por_formulario(client):
    r = client.post("/auth/token", data={"username": "lmartinez@colegio.edu.co", "password": PASSWORD_DEMO})
    assert r.status_code == 200 and r.json()["usuario"]["rol"] == "docente"


def test_endpoint_protegido_sin_token_401(client):
    assert client.get("/comunicados/").status_code == 401
    assert client.get("/comunicados/", headers={"Authorization": "Bearer token-falso"}).status_code == 401


def test_mi_perfil_y_cambio_de_password(client, login):
    h = login("jorge")
    assert client.get("/auth/me", headers=h).json()["correo"] == "jorge.perez@correo.com"
    r = client.patch("/auth/me", json={"telefono": "3009998877"}, headers=h)
    assert r.json()["telefono"] == "3009998877"
    assert client.put("/auth/me/password", json={"password_actual": "otra", "password_nueva": "NuevaClave1"},
                      headers=h).status_code == 400
    assert client.put("/auth/me/password", json={"password_actual": PASSWORD_DEMO, "password_nueva": "NuevaClave1"},
                      headers=h).status_code == 200
    assert _login(client, "jorge.perez@correo.com", "acudiente", "NuevaClave1").status_code == 200


def test_crear_usuario_guarda_password_cifrada(client, login):
    rol_acudiente = next(r["id"] for r in client.get("/catalogos/roles", headers=login("coord")).json()
                         if r["nombre"] == "acudiente")
    r = client.post("/usuarios/", headers=login("coord"), json={
        "nombre": "Pedro Gil", "correo": "pedro@correo.com", "password": "Segura123", "rol_id": rol_acudiente})
    assert r.status_code == 201
    assert "password_hash" not in r.json() and r.json()["rol"] == "acudiente"
    from app.repositories.usuario_repo import UsuarioRepository
    guardado = UsuarioRepository().obtener(r.json()["id"])
    assert guardado["password_hash"].startswith("$2") and guardado["password_hash"] != "Segura123"


def test_correo_duplicado_sin_importar_mayusculas_409(client, login):
    r = client.post("/usuarios/", headers=login("coord"), json={
        "nombre": "Copia", "correo": "Maria.Rodriguez@CORREO.com", "password": "Segura123", "rol_id": 3})
    assert r.status_code == 409
    assert "correo" in r.json()["detail"]


def test_validacion_pydantic_422(client, login):
    r = client.post("/usuarios/", headers=login("coord"), json={
        "nombre": "X", "correo": "no-es-correo", "password": "123", "rol_id": "abc"})
    assert r.status_code == 422


def test_borrado_logico_bloquea_login_y_se_puede_reactivar(client, login, datos):
    ana_id = datos["usuarios"]["acu3"]["id"]
    assert client.delete(f"/usuarios/{ana_id}", headers=login("coord")).status_code == 200
    assert client.get(f"/usuarios/{ana_id}", headers=login("coord")).json()["estado"] == "inactivo"
    assert _login(client, "ana.sanchez@correo.com", "acudiente").status_code == 403
    assert client.post(f"/usuarios/{ana_id}/reactivar", headers=login("coord")).status_code == 200
    assert _login(client, "ana.sanchez@correo.com", "acudiente").status_code == 200


def test_no_puede_desactivarse_a_si_mismo(client, login, datos):
    r = client.delete(f"/usuarios/{datos['usuarios']['coord']['id']}", headers=login("coord"))
    assert r.status_code == 400


def test_filtro_usuarios_por_rol(client, login):
    r = client.get("/usuarios/?rol=acudiente", headers=login("coord"))
    assert r.status_code == 200 and len(r.json()) == 10
    assert all(u["rol"] == "acudiente" for u in r.json())
