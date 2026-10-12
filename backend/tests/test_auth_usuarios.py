from scripts.seed import PASSWORD_DEMO


def test_login_correcto_devuelve_token_y_usuario_sin_hash(client):
    r = client.post("/auth/login", data={"username": "ADMIN@colegio.edu.co", "password": PASSWORD_DEMO})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["access_token"] and cuerpo["usuario"]["rol"] == "admin"
    assert "password_hash" not in cuerpo["usuario"]


def test_login_incorrecto_401(client):
    r = client.post("/auth/login", data={"username": "admin@colegio.edu.co", "password": "malisima"})
    assert r.status_code == 401


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
    assert client.post("/auth/login", data={"username": "jorge.perez@correo.com",
                                            "password": "NuevaClave1"}).status_code == 200


def test_crear_usuario_guarda_password_cifrada(client, login):
    r = client.post("/usuarios/", headers=login("coord"), json={
        "nombre": "Pedro Gil", "correo": "pedro@correo.com", "password": "Segura123", "rol_id": 4})
    assert r.status_code == 201
    assert "password_hash" not in r.json() and r.json()["rol"] == "acudiente"
    from app.repositories.usuario_repo import UsuarioRepository
    guardado = UsuarioRepository().obtener(r.json()["id"])
    assert guardado["password_hash"].startswith("$2") and guardado["password_hash"] != "Segura123"


def test_correo_duplicado_sin_importar_mayusculas_409(client, login):
    r = client.post("/usuarios/", headers=login("admin"), json={
        "nombre": "Copia", "correo": "Maria.Rodriguez@CORREO.com", "password": "Segura123", "rol_id": 4})
    assert r.status_code == 409
    assert "correo" in r.json()["detail"]


def test_validacion_pydantic_422(client, login):
    r = client.post("/usuarios/", headers=login("admin"), json={
        "nombre": "X", "correo": "no-es-correo", "password": "123", "rol_id": "abc"})
    assert r.status_code == 422


def test_permisos_por_rol(client, login):
    assert client.get("/usuarios/", headers=login("maria")).status_code == 403
    r = client.post("/usuarios/", headers=login("coord"), json={
        "nombre": "Otro Admin", "correo": "otro@colegio.edu.co", "password": "Segura123", "rol_id": 1})
    assert r.status_code == 403   # coordinación no puede crear administradores
    assert client.post("/roles/", headers=login("doc1"), json={"nombre": "invitado"}).status_code == 403
    assert client.post("/roles/", headers=login("admin"), json={"nombre": "invitado"}).status_code == 201


def test_borrado_logico_bloquea_login_y_se_puede_reactivar(client, login, datos):
    ana_id = datos["usuarios"]["acu3"]["id"]
    assert client.delete(f"/usuarios/{ana_id}", headers=login("coord")).status_code == 200
    # Sigue existiendo en la BD, solo inactiva
    assert client.get(f"/usuarios/{ana_id}", headers=login("coord")).json()["estado"] == "inactivo"
    assert client.post("/auth/login", data={"username": "ana.sanchez@correo.com",
                                            "password": PASSWORD_DEMO}).status_code == 403
    assert client.post(f"/usuarios/{ana_id}/reactivar", headers=login("coord")).status_code == 200
    assert client.post("/auth/login", data={"username": "ana.sanchez@correo.com",
                                            "password": PASSWORD_DEMO}).status_code == 200


def test_no_puede_desactivarse_a_si_mismo(client, login, datos):
    r = client.delete(f"/usuarios/{datos['usuarios']['coord']['id']}", headers=login("coord"))
    assert r.status_code == 400


def test_filtro_usuarios_por_rol(client, login):
    r = client.get("/usuarios/?rol=acudiente", headers=login("doc1"))
    assert r.status_code == 200 and len(r.json()) == 4
    assert all(u["rol"] == "acudiente" for u in r.json())
